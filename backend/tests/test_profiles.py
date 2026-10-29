def test_catalog_endpoints_return_demo_options(client) -> None:
    colleges = client.get("/api/v1/institutions")
    campuses = client.get("/api/v1/campuses")

    assert colleges.status_code == 200
    assert colleges.json()[0]["institution_type"] == "community_college"
    assert campuses.status_code == 200
    assert campuses.json()[0]["institution_type"] == "university"


def test_create_and_retrieve_student_profile(client) -> None:
    campus = client.get("/api/v1/campuses").json()[0]
    major = client.get(f"/api/v1/majors?institution_id={campus['id']}").json()[0]
    college = client.get("/api/v1/institutions").json()[0]

    response = client.post(
        "/api/v1/student-profiles",
        json={
            "current_college_id": college["id"],
            "anticipated_transfer_term": "Fall 2027",
            "targets": [{"target_campus_id": campus["id"], "intended_major_id": major["id"]}],
        },
    )

    assert response.status_code == 201
    profile_id = response.json()["id"]
    retrieved = client.get(f"/api/v1/student-profiles/{profile_id}")
    assert retrieved.status_code == 200
    assert retrieved.json()["targets"][0]["intended_major"]["id"] == major["id"]


def test_profile_validation_rejects_invalid_campus(client) -> None:
    college = client.get("/api/v1/institutions").json()[0]
    response = client.post(
        "/api/v1/student-profiles",
        json={
            "current_college_id": college["id"],
            "anticipated_transfer_term": "Fall 2027",
            "targets": [{"target_campus_id": 999, "intended_major_id": 999}],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid target campus"


def test_missing_profile_returns_not_found(client) -> None:
    response = client.get("/api/v1/student-profiles/999")

    assert response.status_code == 404
