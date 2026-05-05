import { useEffect, useState } from "react";
import "./Dashboard.css";

function Dashboard({ onLogout }) {
  function loadSavedData(key) {
    try {
      const savedData = localStorage.getItem(key);
      return savedData ? JSON.parse(savedData) : [];
    } catch {
      return [];
    }
  }

  const [notes, setNotes] = useState(() => loadSavedData("notes"));
  const [tasks, setTasks] = useState(() => loadSavedData("tasks"));

  const [noteTitle, setNoteTitle] = useState("");
  const [noteBody, setNoteBody] = useState("");
  const [selectedNoteId, setSelectedNoteId] = useState(null);

  const [summary, setSummary] = useState("");
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    localStorage.setItem("notes", JSON.stringify(notes));
  }, [notes]);

  useEffect(() => {
    localStorage.setItem("tasks", JSON.stringify(tasks));
  }, [tasks]);

  const selectedNote = notes.find((note) => note.id === selectedNoteId);

  function getNoteText(note) {
    if (!note) {
      return "";
    }

    return note.body || note.description || "";
  }

  function saveNote(e) {
    e.preventDefault();

    if (noteTitle.trim() === "" || noteBody.trim() === "") {
      return;
    }

    const newNote = {
      id: Date.now(),
      title: noteTitle.trim(),
      body: noteBody.trim(),
      createdAt: new Date().toLocaleString(),
    };

    setNotes([newNote, ...notes]);
    setSelectedNoteId(newNote.id);
    setNoteTitle("");
    setNoteBody("");
    setSummary("");
    setSuggestions([]);
  }

  function deleteNote(id) {
    setNotes(notes.filter((note) => note.id !== id));

    if (selectedNoteId === id) {
      setSelectedNoteId(null);
      setSummary("");
      setSuggestions([]);
    }
  }

  function generateMockSummary() {
    if (!selectedNote) {
      return;
    }

    const text = getNoteText(selectedNote);
    const shortText = text.length > 180 ? text.substring(0, 180) + "..." : text;

    setSummary(`This note discusses: ${shortText}`);
  }

  function extractMockTasks() {
    if (!selectedNote) {
      return;
    }

    const text = getNoteText(selectedNote);

    const sentences = text
      .split(/[.!?\n]/)
      .map((sentence) => sentence.trim())
      .filter((sentence) => sentence !== "");

    const actionWords = [
      "need to",
      "should",
      "must",
      "finish",
      "prepare",
      "review",
      "test",
      "implement",
      "create",
      "update",
      "fix",
      "follow up",
      "submit",
      "complete",
    ];

    const extractedTasks = sentences.filter((sentence) =>
      actionWords.some((word) => sentence.toLowerCase().includes(word))
    );

    if (extractedTasks.length === 0) {
      setSuggestions([
        "Review this note and identify important follow-up tasks.",
        "Summarize the key points from this note.",
      ]);
    } else {
      setSuggestions(extractedTasks);
    }
  }

  function approveSuggestion(suggestion) {
    const newTask = {
      id: Date.now(),
      title: suggestion,
      sourceNote: selectedNote ? selectedNote.title : "Unknown note",
      completed: false,
    };

    setTasks([newTask, ...tasks]);
    setSuggestions(suggestions.filter((item) => item !== suggestion));
  }

  function dismissSuggestion(suggestion) {
    setSuggestions(suggestions.filter((item) => item !== suggestion));
  }

  function toggleTask(id) {
    setTasks(
      tasks.map((task) =>
        task.id === id ? { ...task, completed: !task.completed } : task
      )
    );
  }

  function deleteTask(id) {
    setTasks(tasks.filter((task) => task.id !== id));
  }

  return (
    <div className="dashboard-layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">D</div>
          <div>
            <h2>DAN</h2>
            <p>Digital Offline Assistant for Notes</p>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button className="active">Dashboard</button>
          <button>Notes</button>
          <button>Tasks</button>
          <button>AI Review</button>
        </nav>

        <button className="logout-button" onClick={onLogout}>
          Log Out
        </button>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <h1>DAN Dashboard</h1>
            <p>Turn messy notes into approved tasks.</p>
          </div>

          <button className="topbar-logout" onClick={onLogout}>
            Log Out
          </button>
        </header>

        <section className="dashboard-grid">
          <div className="card notes-card">
            <div className="card-header">
              <h2>Write a Note</h2>
            </div>

            <form onSubmit={saveNote} className="note-form">
              <input
                type="text"
                placeholder="Note title..."
                value={noteTitle}
                onChange={(e) => setNoteTitle(e.target.value)}
              />

              <textarea
                placeholder="Write your unstructured note here..."
                value={noteBody}
                onChange={(e) => setNoteBody(e.target.value)}
              />

              <button type="submit" className="primary-btn">
                Save Note
              </button>
            </form>

            <h3 className="section-title">Saved Notes</h3>

            {notes.length === 0 ? (
              <p className="empty-message">No notes saved yet.</p>
            ) : (
              <div className="note-list">
                {notes.map((note) => (
                  <div
                    key={note.id}
                    className={
                      selectedNoteId === note.id
                        ? "note-item selected-note"
                        : "note-item"
                    }
                    onClick={() => {
                      setSelectedNoteId(note.id);
                      setSummary("");
                      setSuggestions([]);
                    }}
                  >
                    <div>
                      <h3>{note.title || "Untitled Note"}</h3>
                      <p>{getNoteText(note).substring(0, 90)}...</p>
                      <span>{note.createdAt || "No date"}</span>
                    </div>

                    <button
                      className="delete-small"
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteNote(note.id);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="card ai-card">
            <div className="card-header">
              <h2>AI Review</h2>
            </div>

            {!selectedNote ? (
              <p className="empty-message">
                Select a saved note to summarize or extract tasks.
              </p>
            ) : (
              <>
                <div className="selected-note-box">
                  <h3>{selectedNote.title || "Untitled Note"}</h3>
                  <p>{getNoteText(selectedNote)}</p>
                </div>

                <div className="ai-buttons">
                  <button onClick={generateMockSummary} className="primary-btn">
                    Summarize Note
                  </button>

                  <button onClick={extractMockTasks} className="secondary-btn">
                    Extract Action Items
                  </button>
                </div>

                {summary !== "" && (
                  <>
                    <h3 className="section-title">AI Summary</h3>
                    <div className="summary-box">{summary}</div>
                  </>
                )}

                <h3 className="section-title">AI Suggestions</h3>

                {suggestions.length === 0 ? (
                  <p className="empty-message">
                    No task suggestions generated yet.
                  </p>
                ) : (
                  suggestions.map((suggestion) => (
                    <div className="suggestion-item" key={suggestion}>
                      <p>{suggestion}</p>

                      <div className="suggestion-actions">
                        <button
                          className="approve-btn"
                          onClick={() => approveSuggestion(suggestion)}
                        >
                          Approve
                        </button>

                        <button
                          className="dismiss-btn"
                          onClick={() => dismissSuggestion(suggestion)}
                        >
                          Dismiss
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </>
            )}
          </div>

          <div className="card tasks-card">
            <div className="card-header">
              <h2>Approved Tasks</h2>
            </div>

            {tasks.length === 0 ? (
              <p className="empty-message">
                Approved AI suggestions will appear here.
              </p>
            ) : (
              <div className="task-list">
                {tasks.map((task) => (
                  <div className="task-item" key={task.id}>
                    <input
                      type="checkbox"
                      checked={task.completed}
                      onChange={() => toggleTask(task.id)}
                    />

                    <div className={task.completed ? "completed-task" : ""}>
                      <h3>{task.title}</h3>
                      <p>From note: {task.sourceNote}</p>
                    </div>

                    <button
                      className="delete-small"
                      onClick={() => deleteTask(task.id)}
                    >
                      Delete
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;