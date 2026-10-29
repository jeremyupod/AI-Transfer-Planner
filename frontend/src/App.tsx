import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  createStudentProfile,
  getCampuses,
  getHealth,
  getInstitutions,
  getMajors,
} from './api/client'
import type { Institution, Major, StudentProfile } from './api/client'
import './App.css'

function App() {
  const [backendStatus, setBackendStatus] = useState('Checking backend…')
  const [colleges, setColleges] = useState<Institution[]>([])
  const [campuses, setCampuses] = useState<Institution[]>([])
  const [majors, setMajors] = useState<Major[]>([])
  const [collegeId, setCollegeId] = useState('')
  const [campusId, setCampusId] = useState('')
  const [majorId, setMajorId] = useState('')
  const [transferTerm, setTransferTerm] = useState('Fall 2027')
  const [savedProfile, setSavedProfile] = useState<StudentProfile | null>(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [catalogError, setCatalogError] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [majorsLoading, setMajorsLoading] = useState(false)
  const savingRef = useRef(false)
  const selectedCampusRef = useRef('')

  useEffect(() => {
    // Health and catalog load separately so a database problem is not reported as the API being down.
    getHealth()
      .then((health) => setBackendStatus(`Backend: ${health.status}`))
      .catch(() => setBackendStatus('Backend unavailable'))
    Promise.all([getInstitutions(), getCampuses()])
      .then(([collegeOptions, campusOptions]) => {
        setColleges(collegeOptions)
        setCampuses(campusOptions)
      })
      .catch(() => {
        setCatalogError('Could not load the demonstration catalog. Make sure the API and database are running, and that migrations and the seed script have been applied.')
      })
  }, [])

  useEffect(() => {
    if (!campusId) return
    const controller = new AbortController()
    const isCurrent = () => !controller.signal.aborted && selectedCampusRef.current === campusId
    getMajors(Number(campusId), controller.signal)
      .then((options) => { if (isCurrent()) setMajors(options) })
      .catch(() => { if (isCurrent()) setError('Could not load majors for that campus. Select another campus and retry.') })
      .finally(() => { if (isCurrent()) setMajorsLoading(false) })
    return () => controller.abort()
  }, [campusId])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (savingRef.current) return
    savingRef.current = true
    setIsSaving(true)
    setMessage('')
    setError('')
    try {
      const profile = await createStudentProfile({
        current_college_id: Number(collegeId),
        anticipated_transfer_term: transferTerm,
        targets: [{ target_campus_id: Number(campusId), intended_major_id: Number(majorId) }],
      })
      setSavedProfile(profile)
      setMessage('Profile saved successfully.')
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : 'Could not save profile.')
    } finally {
      savingRef.current = false
      setIsSaving(false)
    }
  }

  return (
    <main className="profile-page">
      <header>
        <p className="eyebrow">AI Transfer Planner</p>
        <h1>Create your transfer profile</h1>
        <p>Choose a starting college, a target campus, a major, and your anticipated transfer term.</p>
        <p className="demo-notice">Demonstration catalog: these limited school and major options are for testing. They are not verified admissions, articulation, or major requirements. Profiles are saved locally without an account.</p>
        <p className="backend-status" role="status">{backendStatus}</p>
        {catalogError && <p className="error" role="alert">{catalogError}</p>}
      </header>

      <form className="profile-form" onSubmit={handleSubmit}>
        <label>
          Current community college
          <select value={collegeId} onChange={(event) => setCollegeId(event.target.value)} required disabled={isSaving}>
            <option value="">Select a college</option>
            {colleges.map((college) => <option key={college.id} value={college.id}>{college.name}</option>)}
          </select>
        </label>
        <label>
          Target UC/CSU campus
          <select value={campusId} onChange={(event) => {
            const value = event.target.value
            selectedCampusRef.current = value
            setCampusId(value)
            setMajors([])
            setMajorId('')
            setMajorsLoading(Boolean(value))
            setError('')
          }} required disabled={isSaving}>
            <option value="">Select a campus</option>
            {campuses.map((campus) => <option key={campus.id} value={campus.id}>{campus.name}</option>)}
          </select>
        </label>
        <label>
          Intended major
          <select value={majorId} onChange={(event) => setMajorId(event.target.value)} required disabled={!campusId || majorsLoading || isSaving}>
            <option value="">{majorsLoading ? 'Loading majors…' : 'Select a major'}</option>
            {majors.map((major) => <option key={major.id} value={major.id}>{major.name}</option>)}
          </select>
        </label>
        <label>
          Anticipated transfer term
          <input value={transferTerm} onChange={(event) => setTransferTerm(event.target.value)} placeholder="Fall 2027" maxLength={40} required disabled={isSaving} aria-describedby="term-help" />
          <small id="term-help">Fall, Winter, Spring, or Summer followed by a year (2000–2199). This records your intention, not campus term availability.</small>
        </label>
        <button type="submit" disabled={isSaving || majorsLoading || !collegeId || !campusId || !majorId}>{isSaving ? 'Saving…' : 'Save profile'}</button>
        {message && <p className="success" role="status">{message}</p>}
        {error && <p className="error" role="alert">{error}</p>}
      </form>

      {savedProfile && (
        <section className="saved-profile">
          <h2>Saved profile</h2>
          <p><strong>College:</strong> {savedProfile.current_college.name}</p>
          <p><strong>Transfer term:</strong> {savedProfile.anticipated_transfer_term}</p>
          {savedProfile.targets.map((target) => <p key={`${target.target_campus.id}-${target.intended_major.id}`}><strong>Target:</strong> {target.target_campus.name} — {target.intended_major.name}</p>)}
        </section>
      )}
    </main>
  )
}

export default App
