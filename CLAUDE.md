# CLAUDE.md

This document provides implementation guidance for Claude Code (and other coding agents) working in this repository.

## 1. Project Overview

PyQtInspect is a runtime inspector for Qt Widgets applications (PyQt5/PyQt6/PySide2/PySide6). Its architecture is split into two cooperating runtimes:

- **Inspector Server (GUI)**: a desktop GUI (`pqi-server`) that developers operate.
- **Debuggee Client (Injected Runtime)**: code running inside the target Python Qt process (`PyQtInspect.pqi` + Qt monkey patches).

At a high level:

1. The client connects to the server over TCP.
2. The client patches Qt widgets/events, tracks widget metadata, and reacts to server commands.
3. The server sends user-driven commands (start inspect, request widget info, execute code, etc.).
4. The client sends structured responses/events back (selected widget info, tree, props, execution result, etc.).

---

## 2. Runtime Architecture and Responsibilities

## 2.1 Server side (GUI)

Primary modules:

- `PyQtInspect/pqi_server_gui.py`: main window and UI orchestration.
- `PyQtInspect/pqi_gui/workers/pqy_worker.py`: TCP listener accepting clients and creating per-client dispatchers.
- `PyQtInspect/pqi_gui/workers/dispatcher.py`: per-connection bridge with reader/writer threads.

Key behavior:

- Server can host **multiple client connections** in detached mode.
- Each accepted socket creates one `Dispatcher`, identified by dispatcher ID.
- UI actions route to a target dispatcher (or all dispatchers) via `PQYWorker` methods.
- Incoming network messages are decoded and dispatched by command ID in `PQIWindow.onWidgetInfoRecv`.

## 2.2 Client side (debuggee runtime)

Primary modules:

- `PyQtInspect/pqi.py`: core debugger/client runtime (`PyDB`) and command handlers.
- `PyQtInspect/_pqi_bundle/pqi_monkey_qt_helpers.py`: Qt patching logic and event interception.
- `PyQtInspect/_pqi_bundle/pqi_comm.py`: network protocol, reader/writer threads, command factory.

Key behavior:

- Client connects to server (`start_client`) and initializes reader/writer threads.
- After successful connect, it sends `CMD_PROCESS_CREATED`.
- After Qt monkey patch success, it sends `CMD_QT_PATCH_SUCCESS` with PID.
- Client stores widget references by `id(widget)` and serves info on demand.
- On server commands, client performs operations like enable inspect, highlight widget, select widget, execute code, return properties/tree/children.

## 2.3 Mode differences

- **Detached mode**: server started explicitly; clients connect to configured host/port.
- **Direct mode**: debuggee launches a colocated server process and exits together with it.

---

## 3. Client/Server Interaction Contract

## 3.1 Transport and framing

- Default protocol is **quoted-line** (one command per line):
  - `cmd_id\tseq\tpayload\n`
- Payload is URL-quoted in `NetCommand`; decoded with `unquote` on read.
- JSON payloads use compact `json.dumps(..., separators=(',', ':'))`.

Implementation anchors:

- `NetCommand` serialization + encoding in `pqi_comm.py`.
- `ReaderThread` parses by newline, then tab-splitting into `cmd_id`, `seq`, `text`.

## 3.2 Command IDs and message semantics

Message IDs are defined in `PyQtInspect/_pqi_bundle/pqi_comm_constants.py`.

Common flows:

- Lifecycle:
  - `CMD_PROCESS_CREATED` (149): client announces connection.
  - `CMD_QT_PATCH_SUCCESS` (1000): client confirms Qt patching and reports PID.
  - `CMD_EXIT` (129): graceful shutdown.
- Inspect control:
  - `CMD_ENABLE_INSPECT` / `CMD_DISABLE_INSPECT`.
  - `CMD_INSPECT_FINISHED` when client-side picking confirms selection.
- Widget information:
  - `CMD_WIDGET_INFO` for detailed widget payload.
  - `CMD_REQ_WIDGET_INFO` request by widget ID + extra metadata.
  - `CMD_REQ_CHILDREN_INFO` / `CMD_CHILDREN_INFO`.
  - `CMD_REQ_CONTROL_TREE` / `CMD_CONTROL_TREE`.
  - `CMD_REQ_WIDGET_PROPS` / `CMD_WIDGET_PROPS`.
- Code execution:
  - `CMD_EXEC_CODE` request.
  - `CMD_EXEC_CODE_RESULT` or `CMD_EXEC_CODE_ERROR` response.

## 3.3 Payload structures

- `QWidgetInfo` and `QWidgetChildrenInfo` dataclasses in `pqi_structures.py` define key response schema.
- Tree payloads use compact key constants in `TreeViewKeys`, `TreeViewResultKeys`, etc. for low transfer overhead.
- Properties payload is a list of property dictionaries (schema produced by widget property fetcher modules).

## 3.4 Processing and dispatch flow

### Server -> Client

1. GUI action triggers worker API call.
2. `PQYWorker` routes command to dispatcher.
3. `Dispatcher` enqueues network command via `WriterThread`.
4. Client `ReaderThread.process_net_command()` maps command ID to `PyDB` method.

### Client -> Server

1. Client side emits command via `NetCommandFactory` + writer.
2. Server `DispatchReader` receives, unquotes, forwards raw message to `Dispatcher.notify()`.
3. `PQIWindow.onWidgetInfoRecv()` switches on command ID and updates UI/state.

---

## 4. Boundary Cases and Reliability Notes

When modifying protocol/runtime code, preserve these behaviors:

1. **Invalid widget pointers**
   - Client side uses `_safe_get_widget` and `is_wrapped_pointer_valid` before operating on widget IDs.
   - If invalid, it silently ignores request and cleans stale cache entry.

2. **Main UI readiness race**
   - `Dispatcher` buffers incoming messages until `registerMainUIReady()` is called.
   - Do not remove this buffer unless replacing with an equivalent ordering guarantee.

3. **Socket lifecycle and shutdown**
   - Writer/reader threads support kill signaling and socket shutdown.
   - Server worker shutdown includes `shutdown(SHUT_RDWR)` before close for Linux behavior.

4. **Reconnect path**
   - `PyDB.finish_debugging_session()` attempts reconnect (`_try_reconnect`) before final teardown.

5. **Payload parsing robustness**
   - `ReaderThread` may receive partial messages; `read_buffer` handles line assembly.
   - Any new payload format must remain line-safe (or evolve protocol end-to-end).

6. **Attach mode patching differences**
   - For attach mode, existing widgets are patched via BFS traversal.
   - PySide and PyQt patching scope differs (PySide may patch many subclasses; PyQt often patches `QWidget`).

---

## 5. Coding Standards

## 5.1 Python style baseline

- Follow **PEP 8** for all Python code:
  - Imports grouped/ordered.
  - Reasonable line lengths and spacing.
  - Descriptive naming.
  - Avoid unused imports/variables.

## 5.2 Qt naming exception (important)

When writing **PyQt/PySide UI code**, use **Qt-style naming** where it improves consistency with the existing codebase and Qt conventions, e.g.:

- UI members like `_selectButton`, `_portLineEdit`, `_mainLayout`.
- Signal names such as `sigWidgetInfoRecv`, `sigClosed`.
- Event-oriented methods like `_onInspectButtonClicked`.

In short: PEP 8 by default, but **Qt-style identifiers are allowed/preferred in Qt-facing code paths**.

## 5.3 Logging requirements

Use logging from `PyQtInspect._pqi_bundle.pqi_log` for critical paths.

- Log key state transitions (connect/disconnect, dispatcher lifecycle, patch success, recoverable errors).
- Keep exception context (`exc_info=True`) when useful.
- Avoid noisy logs inside extremely hot per-event loops unless debug-gated.

Do not introduce ad-hoc print debugging in production code.

---

## 6. Architecture and Change Guidelines

1. **Protocol evolution**
   - If adding command types, update all of:
     - constants (`pqi_comm_constants.py`)
     - factory builder (`NetCommandFactory`)
     - client command handler (`ReaderThread.process_net_command`)
     - server handler (`PQIWindow.onWidgetInfoRecv`)
     - relevant docs (`README.md` and this file when behavior changes)

2. **Compatibility mindset**
   - Existing message IDs and payload keys are part of a compatibility contract between server and client.
   - Prefer additive changes over breaking renames.

3. **Threading awareness**
   - Network reader/writer and Qt UI thread interact indirectly; avoid blocking UI thread.
   - Be careful with state mutations shared across callbacks.

4. **Qt patch safety**
   - Monkey patches run in target process and can destabilize user apps.
   - Prioritize safety checks (`isdeleted`, `ispycreated`, validity checks) over aggressive behavior.

---

## 7. Review Checklist (for feature PRs)

For new features, reviewers and coding agents should verify:

1. **Logging coverage**
   - Critical execution paths are logged via `PyQtInspect._pqi_bundle.pqi_log`.

2. **Regression risk**
   - Evaluate impact on existing flows.
   - If a path touches core communication/patching/runtime state, inspect related code line-by-line.

3. **Documentation updates**
   - Update `README.md` when user-facing behavior, startup flags, compatibility, or workflows change.
   - Include explicit diff-level suggestions in review comments if README updates are incomplete.

---

## 8. Practical Workflow for Claude Code

Before editing:

1. Identify whether the change is in **server GUI**, **client runtime**, or **protocol boundary**.
2. Locate all mirrored handlers on both sides if protocol-affecting.
3. Confirm logging and fallback behavior for error paths.

Before submitting:

1. Run targeted checks/tests relevant to touched modules.
2. Ensure no protocol mismatch between command producers/consumers.
3. Re-check Qt naming consistency in UI modules and PEP 8 elsewhere.
4. Verify whether README changes are required.

