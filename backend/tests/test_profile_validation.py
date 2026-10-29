import pytest
from sqlalchemy import func, select

from app.models import StudentProfile


def profile_payload(client):
    campus = client.get("/api/v1/campuses").json()[0]
    major = client.get("/api/v1/majors", params={"institution_id": campus["id"]}).json()[0]
    return {
        "current_college_id": client.get("/api/v1/institutions").json()[0]["id"],
        "anticipated_transfer_term": "Fall 2027",
        "targets": [{"target_campus_id": campus["id"], "intended_major_id": major["id"]}],
    }


@pytest.mark.parametrize("term", ["", "   ", "Autumn 2027", "Fall 27", "Fall 1999", "Spring 2200", "anything"])
def test_invalid_terms_are_rejected(client, term):
    payload = profile_payload(client)
    payload["anticipated_transfer_term"] = term
    assert client.post("/api/v1/student-profiles", json=payload).status_code == 422


def test_term_normalization(client):
    payload = profile_payload(client)
    payload["anticipated_transfer_term"] = "  spring   2028  "
    response = client.post("/api/v1/student-profiles", json=payload)
    assert response.status_code == 201
    assert response.json()["anticipated_transfer_term"] == "Spring 2028"


@pytest.mark.parametrize("identifier", [0, -1, True, "1", 1.5])
def test_body_ids_must_be_positive_integers(client, identifier):
    payload = profile_payload(client)
    payload["current_college_id"] = identifier
    assert client.post("/api/v1/student-profiles", json=payload).status_code == 422


@pytest.mark.parametrize("path", ["/api/v1/majors?institution_id=0", "/api/v1/majors?institution_id=-1", "/api/v1/student-profiles/0", "/api/v1/institutions?institution_type=invalid"])
def test_invalid_query_and_path_values(client, path):
    assert client.get(path).status_code == 422


def test_duplicate_targets_rejected_without_persisting(client, db_factory):
    payload = profile_payload(client)
    payload["targets"] *= 2
    assert client.post("/api/v1/student-profiles", json=payload).status_code == 422
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(StudentProfile)) == 0


def test_actual_campus_major_mismatch_and_atomic_failure(client, db_factory):
    payload = profile_payload(client)
    other_campus = client.get("/api/v1/campuses").json()[1]
    payload["targets"].append({**payload["targets"][0], "target_campus_id": other_campus["id"]})
    response = client.post("/api/v1/student-profiles", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Major is not associated with target campus"
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(StudentProfile)) == 0


def test_multiple_valid_targets_round_trip(client):
    payload = profile_payload(client)
    other = client.get("/api/v1/campuses").json()[1]
    major = client.get("/api/v1/majors", params={"institution_id": other["id"]}).json()[0]
    payload["targets"].append({"target_campus_id": other["id"], "intended_major_id": major["id"]})
    created = client.post("/api/v1/student-profiles", json=payload)
    assert created.status_code == 201
    targets = client.get(f"/api/v1/student-profiles/{created.json()['id']}").json()["targets"]
    assert [target["target_campus"]["id"] for target in targets] == [t["target_campus_id"] for t in payload["targets"]]


@pytest.mark.parametrize("use_university", [True, False])
def test_current_college_must_be_existing_community_college(client, use_university):
    payload = profile_payload(client)
    payload["current_college_id"] = payload["targets"][0]["target_campus_id"] if use_university else 999
    response = client.post("/api/v1/student-profiles", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid community college"


@pytest.mark.parametrize("count", [0, 11])
def test_target_count_limits(client, count):
    payload = profile_payload(client)
    payload["targets"] = [{"target_campus_id": index + 1, "intended_major_id": 1} for index in range(count)]
    assert client.post("/api/v1/student-profiles", json=payload).status_code == 422


def test_post_preflight(client):
    response = client.options("/api/v1/student-profiles", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
