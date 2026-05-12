import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowRight,
  Bot,
  Brain,
  Check,
  CheckCircle2,
  ClipboardList,
  FileAudio,
  FileText,
  HelpCircle,
  Home,
  Mic,
  Plus,
  RefreshCw,
  Search,
  Server as ServerIcon,
  Settings as SettingsIcon,
  Sparkles,
  Square,
  Trash2,
  Upload,
  X,
} from 'lucide-react';

const API_BASE = 'http://127.0.0.1:8000';

const blankDraft = {
  title: '',
  content: '',
};

const starterNote = {
  title: 'Week 2 demo plan',
  content:
    'Create a short note for the demo. We need to summarize it, extract action items, approve the useful tasks, and ask DAN what the next steps are. Keep the flow simple and make sure Clear Mind works before each new user.',
};

const networkIssuePattern = /failed to fetch|backend offline/i;
const issuePattern = /offline|failed|error|unavailable/i;

const tourSteps = [
  {
    target: '[data-tour="clear-mind"]',
    title: 'Start fresh',
    text: 'Use Clear Mind before a new demo or user. It removes old notes, tasks, uploads, transcripts, and AI suggestions.',
  },
  {
    target: '[data-tour="new-note"]',
    title: 'Create a note',
    text: 'Click New Note, write or paste messy notes, then save. DAN only works from what this user adds.',
  },
  {
    target: '[data-tour="ai-actions"]',
    title: 'Ask for help',
    text: 'Summarize creates a readable overview. Extract finds possible tasks from the current note.',
  },
  {
    target: '[data-tour="review"]',
    title: 'Approve suggestions',
    text: 'AI suggestions do not become tasks automatically. The user approves or dismisses each one.',
  },
  {
    target: '[data-tour="ask"]',
    title: 'Ask DAN',
    text: 'Ask questions about saved notes. After Clear Mind, DAN has nothing old to search from.',
  },
  {
    target: '[data-tour="capture"]',
    title: 'Capture more',
    text: 'Record audio, paste text, or upload a file. DAN turns each input into saved context.',
  },
];

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }
  return response.json();
}

function navItems() {
  return [
    { id: 'dashboard', label: 'Home', icon: Home },
    { id: 'notes', label: 'Notes', icon: FileText },
    { id: 'tasks', label: 'Tasks', icon: ClipboardList },
    { id: 'review', label: 'AI suggestions', icon: Sparkles, tour: 'review' },
    { id: 'ask', label: 'Ask DAN', icon: Bot, tour: 'ask' },
    { id: 'record', label: 'Capture', icon: FileAudio, tour: 'capture' },
  ];
}

export default function App() {
  const [view, setView] = useState('dashboard');
  const [notes, setNotes] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [activeNoteId, setActiveNoteId] = useState(null);
  const [draft, setDraft] = useState(starterNote);
  const [status, setStatus] = useState('Ready');
  const [busy, setBusy] = useState(false);
  const [summary, setSummary] = useState('');
  const [askQuestion, setAskQuestion] = useState('What should we do next?');
  const [askAnswer, setAskAnswer] = useState('');
  const [recording, setRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileImportResult, setFileImportResult] = useState('');
  const [tourIndex, setTourIndex] = useState(null);
  const recorderRef = useRef(null);
  const chunksRef = useRef([]);

  const activeNote = useMemo(
    () => notes.find((note) => note.id === activeNoteId) || notes[0] || null,
    [notes, activeNoteId],
  );

  const openTasks = tasks.filter((task) => task.status !== 'done');
  const approvedTasks = tasks.filter((task) => task.source_ai_suggestion_id);
  const pendingSuggestions = suggestions.filter((item) => item.type === 'task' && item.status === 'draft');
  const latestNotes = notes.slice(0, 5);

  async function refresh() {
    const [noteData, taskData, suggestionData] = await Promise.all([
      api('/api/notes'),
      api('/api/tasks'),
      api('/api/ai/suggestions'),
    ]);
    setNotes(noteData);
    setTasks(taskData);
    setSuggestions(suggestionData);
    setActiveNoteId((current) => {
      if (current && noteData.some((note) => note.id === current)) return current;
      return noteData[0]?.id || null;
    });
  }

  useEffect(() => {
    refresh().catch((error) => setStatus(`Backend offline: ${error.message}`));
  }, []);

  useEffect(() => {
    let cancelled = false;
    const checkBackend = async () => {
      try {
        await api('/health');
        if (!cancelled) {
          setStatus((current) => (networkIssuePattern.test(current) ? 'Ready' : current));
        }
      } catch (error) {
        if (!cancelled) {
          setStatus(`Backend offline: ${error.message}`);
        }
      }
    };
    const timer = window.setInterval(checkBackend, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (activeNote) {
      setDraft({ title: activeNote.title, content: activeNote.content });
    }
  }, [activeNote?.id]);

  async function runAction(label, fn) {
    setBusy(true);
    setStatus(label);
    try {
      await fn();
      setStatus('Done');
    } catch (error) {
      setStatus(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function clearMind() {
    const confirmed = window.confirm(
      'Clear DAN mind for a fresh user? This removes all local notes, tasks, AI suggestions, uploads, and transcripts in this prototype.',
    );
    if (!confirmed) return;
    await runAction('Clearing DAN mind', async () => {
      await api('/api/system/clear-mind', { method: 'POST' });
      setNotes([]);
      setTasks([]);
      setSuggestions([]);
      setActiveNoteId(null);
      setDraft(starterNote);
      setSummary('');
      setAskAnswer('');
      setAskQuestion('What should we do next?');
      setTranscript('');
      setSelectedFile(null);
      setFileImportResult('');
      setView('dashboard');
      await refresh();
    });
  }

  async function saveNote() {
    if (!draft.title.trim() && !draft.content.trim()) {
      setStatus('Write a title or note first');
      return;
    }
    await runAction('Saving note', async () => {
      const payload = {
        title: draft.title.trim() || 'Untitled note',
        content: draft.content,
        source: activeNote?.source || 'manual',
      };
      if (activeNote) {
        const updated = await api(`/api/notes/${activeNote.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
        setActiveNoteId(updated.id);
      } else {
        const created = await api('/api/notes', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        setActiveNoteId(created.id);
      }
      await refresh();
    });
  }

  async function createFreshNote() {
    setActiveNoteId(null);
    setDraft(blankDraft);
    setSummary('');
    setView('notes');
  }

  async function useStarterNote() {
    setActiveNoteId(null);
    setDraft(starterNote);
    setView('notes');
  }

  async function deleteActiveNote() {
    if (!activeNote) return;
    await runAction('Deleting note', async () => {
      await api(`/api/notes/${activeNote.id}`, { method: 'DELETE' });
      setActiveNoteId(null);
      setDraft(starterNote);
      setSummary('');
      await refresh();
    });
  }

  async function summarizeActiveNote() {
    const noteId = await ensureSavedNote();
    if (!noteId) return;
    await runAction('Summarizing note', async () => {
      const result = await api('/api/ai/summarize', {
        method: 'POST',
        body: JSON.stringify({ note_id: noteId }),
      });
      setSummary(result.summary);
      await refresh();
      setView('review');
    });
  }

  async function extractActiveActions() {
    const noteId = await ensureSavedNote();
    if (!noteId) return;
    await runAction('Extracting action items', async () => {
      await api('/api/ai/extract-actions', {
        method: 'POST',
        body: JSON.stringify({ note_id: noteId }),
      });
      await refresh();
      setView('review');
    });
  }

  async function ensureSavedNote() {
    if (activeNote) return activeNote.id;
    if (!draft.title.trim() && !draft.content.trim()) {
      setStatus('Create or save a note first');
      return null;
    }
    const created = await api('/api/notes', {
      method: 'POST',
      body: JSON.stringify({
        title: draft.title.trim() || 'Untitled note',
        content: draft.content,
        source: 'manual',
      }),
    });
    setActiveNoteId(created.id);
    await refresh();
    return created.id;
  }

  async function rewriteActiveNote() {
    const noteId = await ensureSavedNote();
    if (!noteId) return;
    await runAction('Cleaning note', async () => {
      const result = await api('/api/ai/rewrite', {
        method: 'POST',
        body: JSON.stringify({ note_id: noteId }),
      });
      setDraft({ title: draft.title || activeNote?.title || 'Cleaned note', content: result.rewritten });
      setView('notes');
    });
  }

  async function approveSuggestion(item) {
    await runAction('Approving task', async () => {
      await api(`/api/ai/suggestions/${item.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({}),
      });
      await refresh();
    });
  }

  async function dismissSuggestion(item) {
    await runAction('Dismissing suggestion', async () => {
      await api(`/api/ai/suggestions/${item.id}/dismiss`, { method: 'POST' });
      await refresh();
    });
  }

  async function toggleTask(task) {
    await runAction('Updating task', async () => {
      await api(`/api/tasks/${task.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          ...task,
          status: task.status === 'done' ? 'open' : 'done',
        }),
      });
      await refresh();
    });
  }

  async function askDan() {
    await runAction('Asking DAN', async () => {
      const result = await api('/api/ai/ask', {
        method: 'POST',
        body: JSON.stringify({ question: askQuestion }),
      });
      setAskAnswer(result.answer);
    });
  }

  async function uploadTextAsNote() {
    await runAction('Importing text', async () => {
      const result = await api('/api/uploads/text', {
        method: 'POST',
        body: JSON.stringify({
          title: 'Imported transcript',
          content: transcript || starterNote.content,
          create_note: true,
        }),
      });
      await refresh();
      setActiveNoteId(result.note.id);
      setView('notes');
    });
  }

  async function uploadSelectedFile() {
    if (!selectedFile) {
      setStatus('Choose a file first');
      return;
    }
    await runAction('Importing file', async () => {
      const form = new FormData();
      form.append('file', selectedFile);
      form.append('title', selectedFile.name.replace(/\.[^/.]+$/, ''));
      form.append('create_note', 'true');
      const response = await fetch(`${API_BASE}/api/uploads/file`, {
        method: 'POST',
        body: form,
      });
      if (!response.ok) throw new Error(await response.text());
      const result = await response.json();
      setFileImportResult(`${result.characters} characters imported`);
      await refresh();
      if (result.note) setActiveNoteId(result.note.id);
      setSelectedFile(null);
      setView('notes');
    });
  }

  async function startRecording() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size) chunksRef.current.push(event.data);
      };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await uploadAudio(blob);
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setStatus('Recording');
    } catch (error) {
      setStatus(`Microphone unavailable: ${error.message}`);
    }
  }

  function stopRecording() {
    recorderRef.current?.stop();
    setRecording(false);
  }

  async function uploadAudio(blob) {
    await runAction('Uploading audio', async () => {
      const form = new FormData();
      form.append('file', blob, `dan-recording-${Date.now()}.webm`);
      form.append('title', 'Recorded note');
      form.append('create_note', 'true');
      const response = await fetch(`${API_BASE}/api/uploads/audio`, {
        method: 'POST',
        body: form,
      });
      if (!response.ok) throw new Error(await response.text());
      const result = await response.json();
      setTranscript(result.transcription.text);
      await refresh();
      if (result.note) setActiveNoteId(result.note.id);
      setView('record');
    });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-line">
            <div>
              <strong>DAN</strong>
              <span>Local AI assistant</span>
            </div>
            <div className="brand-mark" aria-hidden="true">
              <Bot size={19} />
            </div>
          </div>
          <div className="prototype-badge">Week 2 Prototype</div>
        </div>

        <nav>
          {navItems().map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={view === item.id ? 'nav-item active' : 'nav-item'}
                onClick={() => setView(item.id)}
                title={item.label}
                data-tour={item.tour}
              >
                <Icon size={17} />
                <span>{item.label}</span>
                {item.id === 'review' && pendingSuggestions.length > 0 && <em>{pendingSuggestions.length}</em>}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="sidebar-actions">
            <button className="primary full" onClick={createFreshNote} data-tour="new-note">
              <Plus size={17} />
              New Note
            </button>
            <button className="secondary full" onClick={() => setTourIndex(0)}>
              <HelpCircle size={17} />
              Tutorial
            </button>
            <button className="ghost-danger full" onClick={clearMind} data-tour="clear-mind">
              <RefreshCw size={17} />
              Clear Mind
            </button>
            <button
              className={view === 'settings' ? 'secondary full utility-active' : 'secondary full'}
              onClick={() => setView('settings')}
              title="Settings"
            >
              <SettingsIcon size={17} />
              Settings
            </button>
          </div>
        </div>

      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="mono-label">Week 2 prototype demo</p>
            <h1>{titleForView(view)}</h1>
          </div>
          <div className="topbar-actions">
            <button className="secondary" onClick={() => setTourIndex(0)}>
              <HelpCircle size={16} />
              Guide
            </button>
            <StatusPill busy={busy} status={status} />
          </div>
        </header>

        {view === 'dashboard' && (
          <section className="today-page">
            <div className="today-hero">
              <p className="mono-label">Local workspace</p>
              <h2>Capture notes. Find next steps.</h2>
              <p className="hero-copy">Demo build for Week 2: add context, summarize fast, and approve the tasks that matter.</p>
              <div className="hero-actions">
                <button className="primary" onClick={createFreshNote}>
                  <Plus size={17} />
                  New blank note
                </button>
                <button className="secondary" onClick={useStarterNote}>
                  <FileText size={17} />
                  Use demo note
                </button>
                <button className="secondary" onClick={() => setView('record')}>
                  <Upload size={17} />
                  Import text
                </button>
              </div>
            </div>

            <div className="metric-row">
              <Metric icon={FileText} label="Notes" value={notes.length} hint="saved" />
              <Metric icon={ClipboardList} label="Open tasks" value={openTasks.length} hint="waiting" />
              <Metric icon={CheckCircle2} label="AI tasks" value={approvedTasks.length} hint="approved" />
              <Metric icon={Sparkles} label="Review" value={pendingSuggestions.length} hint="suggestions" />
            </div>

            <div className="dashboard-grid">
              <div className="panel span-2">
                <PanelHeader icon={FileText} title="Recent notes" />
                <div className="note-list compact">
                  {latestNotes.length ? (
                    latestNotes.map((note) => (
                      <button key={note.id} onClick={() => { setActiveNoteId(note.id); setView('notes'); }}>
                        <strong>{note.title}</strong>
                        <span>{note.content.slice(0, 140) || 'Empty note'}</span>
                      </button>
                    ))
                  ) : (
                    <EmptyState
                      title="No notes yet"
                      text="Create a note or import transcript text to give DAN something to work with."
                      action="Create note"
                      onAction={createFreshNote}
                    />
                  )}
                </div>
              </div>
              <div className="panel span-2">
                <PanelHeader icon={Sparkles} title="Next best step" />
                <div className="workflow-card">
                  <ol>
                    <li>Create or import a note.</li>
                    <li>Summarize the note.</li>
                    <li>Extract action items.</li>
                    <li>Approve useful tasks.</li>
                  </ol>
                  <button className="primary" onClick={() => setView('notes')}>
                    Continue
                    <ArrowRight size={17} />
                  </button>
                </div>
              </div>
            </div>
          </section>
        )}

        {view === 'notes' && (
          <section className="notes-layout">
            <div className="note-browser">
              <div className="search-strip">
                <Search size={15} />
                <span>Notes in this mind</span>
              </div>
              <div className="note-list">
                {notes.map((note) => (
                  <button
                    key={note.id}
                    className={activeNote?.id === note.id ? 'selected' : ''}
                    onClick={() => setActiveNoteId(note.id)}
                  >
                    <strong>{note.title}</strong>
                    <span>{note.content.slice(0, 120) || 'Empty note'}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="editor-surface">
              <div className="editor-actions" data-tour="ai-actions">
                <button className="secondary" onClick={summarizeActiveNote} disabled={busy}>
                  <Sparkles size={17} />
                  Summarize
                </button>
                <button className="secondary" onClick={extractActiveActions} disabled={busy}>
                  <ClipboardList size={17} />
                  Extract tasks
                </button>
                <button className="secondary" onClick={rewriteActiveNote} disabled={busy}>
                  <Bot size={17} />
                  Clean note
                </button>
                <button className="icon danger" onClick={deleteActiveNote} title="Delete note" disabled={!activeNote}>
                  <Trash2 size={18} />
                </button>
              </div>
              <input
                className="title-input"
                value={draft.title}
                onChange={(event) => setDraft({ ...draft, title: event.target.value })}
                placeholder="Untitled note"
              />
              <textarea
                className="note-editor"
                value={draft.content}
                onChange={(event) => setDraft({ ...draft, content: event.target.value })}
                placeholder="Write or paste the user's notes here. DAN will only use saved notes from this fresh mind."
              />
              <div className="editor-footer">
                <p>Tip: save first, then run AI so suggestions attach to this note.</p>
                <button className="primary" onClick={saveNote} disabled={busy}>
                  <Check size={18} />
                  Save note
                </button>
              </div>
            </div>
          </section>
        )}

        {view === 'tasks' && (
          <section className="panel narrow-page">
            <PanelHeader icon={ClipboardList} title="Tasks" />
            <div className="task-list">
              {tasks.length ? (
                tasks.map((task) => (
                  <button key={task.id} className={task.status === 'done' ? 'task done' : 'task'} onClick={() => toggleTask(task)}>
                    <span className="check-dot">{task.status === 'done' && <Check size={14} />}</span>
                    <span>
                      <strong>{task.title}</strong>
                      <small>{task.description || 'No description'}</small>
                    </span>
                    <em>{task.priority}</em>
                  </button>
                ))
              ) : (
                <EmptyState
                  title="No tasks yet"
                  text="Extract action items from a note, then approve the useful ones here."
                  action="Go to notes"
                  onAction={() => setView('notes')}
                />
              )}
            </div>
          </section>
        )}

        {view === 'review' && (
          <section className="review-layout">
            <div className="panel">
              <PanelHeader icon={Sparkles} title="Summary" />
              <div className="summary-box">{summary || 'Run Summarize on a note to fill this panel.'}</div>
            </div>
            <div className="panel" data-tour="review">
              <PanelHeader icon={ClipboardList} title="Suggested tasks" />
              <SuggestionList suggestions={pendingSuggestions} onApprove={approveSuggestion} onDismiss={dismissSuggestion} />
            </div>
          </section>
        )}

        {view === 'ask' && (
          <section className="ask-layout" data-tour="ask">
            <div className="panel">
              <PanelHeader icon={Bot} title="Ask DAN" />
              <p className="subtle-copy">DAN searches only this local mind. Use Clear Mind to remove old context before a new user.</p>
              <div className="ask-row">
                <input value={askQuestion} onChange={(event) => setAskQuestion(event.target.value)} />
                <button className="primary" onClick={askDan} disabled={busy}>
                  <Search size={18} />
                  Ask
                </button>
              </div>
              <div className="answer-box">{askAnswer || 'Ask a question after adding notes.'}</div>
            </div>
          </section>
        )}

        {view === 'record' && (
          <section className="record-layout" data-tour="capture">
            <div className="panel capture-card">
              <PanelHeader icon={Mic} title="Record audio" />
              <p className="subtle-copy">Record audio in the browser. The backend tries local transcription and falls back safely if needed.</p>
              <div className="capture-surface">
                <Mic size={24} />
                <strong>{recording ? 'Recording now' : 'Browser audio'}</strong>
                <span>{recording ? 'Stop when you are done speaking.' : 'Create a note from spoken context.'}</span>
              </div>
              <div className="record-controls capture-actions">
                {!recording ? (
                  <button className="primary" onClick={startRecording}>
                    <Mic size={18} />
                    Record
                  </button>
                ) : (
                  <button className="danger-button" onClick={stopRecording}>
                    <Square size={18} />
                    Stop
                  </button>
                )}
              </div>
            </div>
            <div className="panel capture-card">
              <PanelHeader icon={FileText} title="Text import" />
              <p className="subtle-copy">Paste transcripts, lecture notes, meeting notes, or rough thoughts.</p>
              <textarea
                className="transcript-box"
                value={transcript}
                onChange={(event) => setTranscript(event.target.value)}
                placeholder="Paste transcript, lecture notes, meeting notes, or a rough brain dump..."
              />
              <button className="primary" onClick={uploadTextAsNote}>
                <Plus size={18} />
                Create note
              </button>
            </div>
            <div className="panel capture-card">
              <PanelHeader icon={Upload} title="File import" />
              <p className="subtle-copy">Upload readable context from TXT, MD, CSV, JSON, HTML, XML, LOG, code, or DOCX.</p>
              <label className="file-drop">
                <input
                  type="file"
                  accept=".txt,.md,.csv,.json,.html,.htm,.xml,.log,.py,.js,.jsx,.ts,.tsx,.css,.sql,.docx,text/*,application/json,application/xml,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={(event) => {
                    setSelectedFile(event.target.files?.[0] || null);
                    setFileImportResult('');
                  }}
                />
                <Upload size={22} />
                <strong>{selectedFile ? selectedFile.name : 'Choose a file'}</strong>
                <span>{selectedFile ? 'Ready to import as a note' : 'Adds the file text into DAN context'}</span>
              </label>
              {fileImportResult && <p className="import-result">{fileImportResult}</p>}
              <button className="primary" onClick={uploadSelectedFile} disabled={!selectedFile || busy}>
                <Plus size={18} />
                Import file
              </button>
            </div>
          </section>
        )}

        {view === 'settings' && (
          <section className="settings-page">
            <div className="settings-hero">
              <p className="mono-label">System map</p>
              <h2>How DAN works.</h2>
              <p>
                DAN is a local-first assistant. The frontend captures notes and actions, the backend stores clean
                data, and the local LLM helps summarize, rewrite, search, and suggest tasks.
              </p>
            </div>

            <div className="architecture-flow" aria-label="DAN architecture flow">
              <FlowNode icon={Home} title="React UI" text="Notes, tasks, capture, review" />
              <span className="flow-arrow">→</span>
              <FlowNode icon={ServerIcon} title="FastAPI" text="Routes, validation, services" />
              <span className="flow-arrow">→</span>
              <FlowNode icon={FileText} title="SQLite" text="Local notes, tasks, uploads" />
              <span className="flow-arrow">→</span>
              <FlowNode icon={Brain} title="Ollama + Gemma" text="Local summaries and suggestions" />
            </div>

            <div className="settings-grid">
              <InfoCard
                icon={Upload}
                kicker="Input"
                title="Context enters DAN"
                text="A user can write a note, paste text, upload a readable file, or record audio. Each input becomes local context before AI features use it."
                tags={['Notes', 'Uploads', 'Audio fallback']}
              />
              <InfoCard
                icon={ServerIcon}
                kicker="Backend"
                title="FastAPI controls the work"
                text="The backend exposes REST routes for notes, tasks, uploads, and AI actions. It keeps frontend code simple and gives the team clear integration points."
                tags={['/api/notes', '/api/tasks', '/api/ai/*']}
              />
              <InfoCard
                icon={FileText}
                kicker="Storage"
                title="SQLite keeps it local"
                text="Notes, tasks, suggestions, uploads, and transcripts are saved in a local SQLite database. Search starts with lightweight local text search."
                tags={['SQLite', 'FTS search', 'Local data']}
              />
              <InfoCard
                icon={Brain}
                kicker="AI"
                title="Gemma runs through Ollama"
                text="When the user clicks Summarize or Extract tasks, FastAPI builds a prompt, calls Ollama locally, then parses the model response into usable app data."
                tags={['Ollama', 'Gemma', 'No paid API']}
              />
              <InfoCard
                icon={CheckCircle2}
                kicker="Safety"
                title="AI suggests, user decides"
                text="AI-generated task ideas are saved as suggestions first. They only become real tasks after the user approves them in the review screen."
                tags={['Approval flow', 'Editable tasks', 'Clear Mind']}
              />
              <InfoCard
                icon={Search}
                kicker="Ask DAN"
                title="Answers come from saved context"
                text="Ask DAN searches the current local notes first, sends matched context to the model, and avoids pretending it knows information the user never added."
                tags={['Search', 'Matched notes', 'Fresh mind']}
              />
            </div>

            <div className="panel settings-stack">
              <PanelHeader icon={SettingsIcon} title="Current stack" />
              <div className="stack-row">
                <TechPill label="React + Vite" />
                <TechPill label="FastAPI" />
                <TechPill label="SQLite" />
                <TechPill label="Ollama" />
                <TechPill label="Gemma" />
                <TechPill label="Pytest" />
              </div>
            </div>
          </section>
        )}
      </main>

      {tourIndex !== null && (
        <TourOverlay
          step={tourSteps[tourIndex]}
          index={tourIndex}
          total={tourSteps.length}
          onClose={() => setTourIndex(null)}
          onPrev={() => setTourIndex(Math.max(0, tourIndex - 1))}
          onNext={() => {
            if (tourIndex === tourSteps.length - 1) setTourIndex(null);
            else setTourIndex(tourIndex + 1);
          }}
        />
      )}
    </div>
  );
}

function titleForView(view) {
  const titles = {
    dashboard: 'Home',
    notes: 'Notes',
    tasks: 'Tasks',
    review: 'AI suggestions',
    ask: 'Ask DAN',
    record: 'Capture',
    settings: 'Settings',
  };
  return titles[view] || 'DAN';
}

function StatusPill({ busy, status }) {
  const hasIssue = issuePattern.test(status || '');
  const hasNetworkIssue = networkIssuePattern.test(status || '');
  const hasAiIssue = /ai|ollama|gemma|model/i.test(status || '') && hasIssue;
  const label = hasNetworkIssue
    ? 'Backend disconnected'
    : hasAiIssue
      ? 'AI needs attention'
      : hasIssue
        ? 'Core needs attention'
        : busy
          ? 'Core running'
          : 'Core working';

  return (
    <div className={hasIssue ? 'status-pill has-issue' : busy ? 'status-pill is-busy' : 'status-pill'} title={status}>
      <span className="core-orbit" aria-hidden="true">
        <Brain size={16} />
        <i />
      </span>
      <span>{label}</span>
      {!hasIssue && <CheckCircle2 size={16} className="core-check" />}
    </div>
  );
}

function Metric({ icon: Icon, label, value, hint }) {
  return (
    <div className="metric">
      <div className="metric-icon">
        <Icon size={18} />
      </div>
      <div>
        <strong>{value}</strong>
        <span>{label}</span>
        <small>{hint}</small>
      </div>
    </div>
  );
}

function PanelHeader({ icon: Icon, title }) {
  return (
    <div className="panel-header">
      <Icon size={18} />
      <h2>{title}</h2>
    </div>
  );
}

function FlowNode({ icon: Icon, title, text }) {
  return (
    <div className="flow-node">
      <div className="flow-icon">
        <Icon size={18} />
      </div>
      <strong>{title}</strong>
      <span>{text}</span>
    </div>
  );
}

function InfoCard({ icon: Icon, kicker, title, text, tags }) {
  return (
    <div className="info-card">
      <div className="info-card-top">
        <div className="metric-icon">
          <Icon size={18} />
        </div>
        <p className="mono-label">{kicker}</p>
      </div>
      <h3>{title}</h3>
      <p>{text}</p>
      <div className="tag-row">
        {tags.map((tag) => (
          <TechPill key={tag} label={tag} />
        ))}
      </div>
    </div>
  );
}

function TechPill({ label }) {
  return <span className="tech-pill">{label}</span>;
}

function EmptyState({ title, text, action, onAction }) {
  return (
    <div className="empty-state">
      <strong>{title}</strong>
      <span>{text}</span>
      {action && (
        <button className="secondary" onClick={onAction}>
          {action}
        </button>
      )}
    </div>
  );
}

function SuggestionList({ suggestions, onApprove, onDismiss }) {
  if (!suggestions.length) {
    return (
      <EmptyState
        title="No pending suggestions"
        text="Open a note, click Extract tasks, then approve only the tasks that make sense."
      />
    );
  }
  return (
    <div className="suggestion-list">
      {suggestions.map((item) => (
        <div className="suggestion" key={item.id}>
          <div>
            <strong>{item.title}</strong>
            <p>{item.content}</p>
          </div>
          <div className="suggestion-actions">
            <button className="icon approve" onClick={() => onApprove(item)} title="Approve task">
              <Check size={18} />
            </button>
            <button className="icon" onClick={() => onDismiss(item)} title="Dismiss suggestion">
              <X size={18} />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function TourOverlay({ step, index, total, onClose, onPrev, onNext }) {
  const [rect, setRect] = useState(null);

  useEffect(() => {
    function updateRect() {
      const element = document.querySelector(step.target);
      if (!element) {
        setRect(null);
        return;
      }
      const next = element.getBoundingClientRect();
      setRect({
        top: next.top,
        left: next.left,
        width: next.width,
        height: next.height,
      });
    }
    updateRect();
    window.addEventListener('resize', updateRect);
    window.addEventListener('scroll', updateRect, true);
    return () => {
      window.removeEventListener('resize', updateRect);
      window.removeEventListener('scroll', updateRect, true);
    };
  }, [step.target]);

  const cardStyle = getTourCardStyle(rect);
  const highlightStyle = rect
    ? {
        top: rect.top - 8,
        left: rect.left - 8,
        width: rect.width + 16,
        height: rect.height + 16,
      }
    : {};

  return (
    <div className="tour-layer">
      <div className="tour-scrim" />
      {rect && <div className="tour-highlight" style={highlightStyle} />}
      <div className="tour-card" style={cardStyle}>
        <div className="tour-arrow" />
        <p className="mono-label">Step {index + 1} of {total}</p>
        <h3>{step.title}</h3>
        <p>{step.text}</p>
        <div className="tour-actions">
          <button className="secondary" onClick={onClose}>Close</button>
          <button className="secondary" onClick={onPrev} disabled={index === 0}>Back</button>
          <button className="primary" onClick={onNext}>
            {index === total - 1 ? 'Finish' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  );
}

function getTourCardStyle(rect) {
  if (!rect) {
    return { top: 120, left: '50%', transform: 'translateX(-50%)' };
  }
  const width = 330;
  const spaceRight = window.innerWidth - (rect.left + rect.width);
  const left = spaceRight > width + 40 ? rect.left + rect.width + 24 : Math.max(18, rect.left - width - 24);
  const top = Math.min(Math.max(18, rect.top), window.innerHeight - 260);
  return { top, left, width };
}
