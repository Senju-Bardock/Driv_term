# Driv_term

**Google Drive in your terminal.** Browse, view, download, upload and organize your Google Drive files from a plain text console, on Windows, Linux and macOS.

Driv_term is a single Python script that uses **only the Python standard library**. There is nothing to `pip install`, no SDK, and no background service. It talks directly to the official Google Drive API v3 over HTTPS and is built for speed: parallel transfers, persistent connections, chunked downloads and resumable uploads.

---

## Table of contents

1. [Features](#features)
2. [Repository contents](#repository-contents)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [First-time setup: getting Google OAuth credentials](#first-time-setup-getting-google-oauth-credentials)
6. [Running the app](#running-the-app)
7. [Signing in (OAuth flow)](#signing-in-oauth-flow)
8. [The main screen](#the-main-screen)
9. [Command reference](#command-reference)
10. [Selecting several items](#selecting-several-items)
11. [Working with files](#working-with-files)
12. [Downloading](#downloading)
13. [Uploading](#uploading)
14. [Moving to trash](#moving-to-trash)
15. [Google Docs, Sheets and Slides](#google-docs-sheets-and-slides)
16. [Performance tuning](#performance-tuning)
17. [Where your data is stored](#where-your-data-is-stored)
18. [Security and privacy](#security-and-privacy)
19. [Command-line options](#command-line-options)
20. [How it works internally](#how-it-works-internally)
21. [Limitations](#limitations)
22. [Troubleshooting](#troubleshooting)
23. [FAQ](#faq)

---

## Features

- **Full Drive navigation** from the keyboard: folders, "Shared with me", and name search.
- **Parallel transfers.** Several files are downloaded or uploaded at the same time using a thread pool (8 threads by default, configurable).
- **Persistent HTTPS connections.** No new DNS lookup, TCP connection and TLS handshake for every request, which makes a big difference with many small files.
- **Chunked parallel downloads.** Large files are split into 16 MiB parts that are downloaded simultaneously with HTTP `Range` requests.
- **Fast recursive folder download.** The folder tree is listed in batches and in parallel instead of one request per folder.
- **Smart uploads.** Small files (up to 5 MiB) go in a single multipart request. Large files use Drive's resumable upload protocol with 16 MiB chunks and automatic recovery after network failures.
- **Whole-folder upload and download**, preserving the directory structure.
- **Friendly upload picker.** Press `u` and choose files and folders with your system's file dialog (several at once). No more typing long paths. Without a graphical interface (SSH, servers) it falls back to typed paths automatically.
- **Download and delete several items at once.** `d 1-3,5` downloads files and folders in a single batch with one progress bar, and `t 2,4-6` moves them to the trash. `all` selects everything.
- **One global progress bar** with total size, percentage, current speed and estimated time remaining.
- **Built-in viewer.** Read text files, Google Docs, Slides and the first sheet of a Google Sheet directly in the terminal, with paging. Other files are opened with your system's default application.
- **Automatic export** of native Google files (Docs, Sheets, Slides, Drawings) to Office/PDF/PNG formats.
- **Safe OAuth 2.0 sign-in** using the loopback flow with PKCE. Your Google password is never typed into or seen by the program.
- **Robust networking.** Automatic retries with exponential backoff, transparent token refresh, and cancellation with `Ctrl+C`.
- **Cross-platform.** Windows, Linux and macOS.
- **Bilingual.** English and Spanish versions are included.

---

## Repository contents

| Path | Description |
| --- | --- |
| `code/Driv_term_en.py` | Python source code, **English** interface. |
| `code/Driv_term_es.py` | Python source code, **Spanish** interface. |
| `Driv_term_en.exe` | Ready-to-run Windows executable, **English** interface. |
| `Driv_term_es.exe` | Ready-to-run Windows executable, **Spanish** interface. |
| `README.md` | This document. |

> If you prefer not to run a pre-built binary, run the Python source from the `code/` folder instead. It is a single readable file and you can inspect everything it does.

---

## Requirements

### Using the Python source

- **Python 3.8 or newer.**
- Internet access.
- A web browser on the same computer (needed once to authorize the app).
- Your own Google OAuth credentials (free, see [below](#first-time-setup-getting-google-oauth-credentials)).

No third-party packages are needed.

### Using the `.exe` files

- Windows.
- A web browser, internet access and your own Google OAuth credentials.
- You do **not** need Python installed.

---

## Installation

### Option A: Python source (all platforms)

```bash
git clone https://github.com/Senju-Bardock/Driv_term.git
cd Driv_term/code
python3 Driv_term_en.py
```

On Windows, use `python` instead of `python3`. Use `Driv_term_es.py` instead for the Spanish interface.

### Option B: Windows executable

1. Download `Driv_term_en.exe` (English) or `Driv_term_es.exe` (Spanish) from this repository.
2. Double-click it, or run it from `cmd` / PowerShell:

```powershell
.\Driv_term_en.exe
```

Windows SmartScreen or your antivirus may warn about unsigned executables downloaded from the internet. This is common for small independent tools. If you are unsure, build and run from the Python source.

---

## First-time setup: getting Google OAuth credentials

Google does not allow third-party programs to use a username and password. Instead, every user creates their **own** free OAuth client, so the app can access **only your** Drive and nobody else's. You do this **once**.

1. Open the [Google Cloud Console](https://console.cloud.google.com/) and **create a project** (any name).
2. Go to **APIs & Services → Library**, search for **Google Drive API** and click **Enable**.
3. Go to **APIs & Services → OAuth consent screen**:
   - Choose user type **External**.
   - Fill in the required app information (app name, your email).
   - Under **Test users**, **add your own Google email address**.
4. Go to **APIs & Services → Credentials → Create credentials → OAuth client ID**:
   - Application type: **Desktop app**.
5. **Download the JSON file** (or copy the *client ID* and *client secret*).

When you launch Driv_term for the first time, it asks for these credentials:

```
Path to the downloaded JSON (or press Enter to paste ID and secret by hand):
```

- Type the path to the downloaded JSON file, **or**
- press Enter and paste the `client_id` and `client_secret` manually.

They are saved locally in `~/.drive_terminal/config.json` and you will not be asked again.

---

## Running the app

Launch the program, then enter the email address of the Google account you want to use:

```
=== Google Drive in the terminal ===

email: you@gmail.com
```

On success you will see:

```
Connected as you@gmail.com
Space used: 12.3 GB of 15.0 GB
Parallel transfers: 8 threads (use DRIVE_WORKERS to change it)
```

and then the main browser screen opens.

---

## Signing in (OAuth flow)

The first time you use an account (or after the saved session expires), Driv_term starts the authorization process:

1. It starts a tiny web server on `127.0.0.1` using a random free port. This only listens on your own computer.
2. It opens your default browser on Google's consent page. If the browser does not open, the program prints a link you can paste into any browser **on the same computer**.
3. You sign in and grant access.
4. Google redirects the browser back to the local server, the page shows **"Done. You can now close this tab"**, and the program continues.
5. A refresh token is stored so future launches sign in automatically.

Details:

- The program waits up to **5 minutes** for you to authorize. Press `Ctrl+C` to cancel.
- The flow uses **PKCE** (S256) and a random `state` value to protect against interception and forgery.
- If you sign in with a different Google account than the email you typed, the program warns you and uses the account you actually signed in with.
- While your app is in "Testing" mode, Google shows a warning screen saying the app is not verified. This is normal because it is *your own* app: click **Advanced** and continue.

---

## The main screen

```
=== Drive: you@gmail.com ===
Path: My Drive / Projects

   #  Type  Name                              Size  Modified
------------------------------------------------------------
   1  DIR   Backups                              -   2026-10-01
   2  DIR   Photos                               -   2026-09-14
   3  GDOC  Meeting notes                        -   2026-10-20
   4  FILE  report.pdf                      2.4 MB   2026-10-18
   5  LNK   Shortcut to archive                  -   2026-08-02

Page 1/1 - 5 items
  [number] open | b back | h home | n/p page | s search | c shared with me
  d SEL download | t SEL trash | u upload | m new folder   (SEL: 3 | 1-4 | 1,3,7 | all)
  r reload | x log out | q quit   (Ctrl+C cancels a transfer)

>
```

**Columns**

| Column | Meaning |
| --- | --- |
| `#` | The number you type to open an item or to use with `d` and `t`. |
| `Type` | `DIR` folder, `FILE` regular file, `GDOC` native Google file (Docs/Sheets/Slides/Drawings), `LNK` shortcut. |
| `Name` | Item name (truncated with `~` if too long for your terminal width). |
| `Size` | Human-readable size (`-` for folders and Google-native files). |
| `Modified` | Last modification date (`YYYY-MM-DD`). |

Folders are listed first, then files, both sorted by name. The list is paginated with **15 items per page**. The layout adapts to the width of your terminal.

---

## Command reference

Type a command at the `>` prompt and press Enter.

| Command | Action |
| --- | --- |
| `<number>` | Open a folder, or open the file menu for a file. Shortcuts are followed to their target. |
| `b` | Go back one level. |
| `h` | Go back to the root ("My Drive"). |
| `n` / `p` | Next / previous page. |
| `s` | Search by name (items whose name *contains* the text you type). |
| `c` | Show files **shared with you**. |
| `d SEL` | Download one or **several** items (files and/or folders), e.g. `d 3`, `d 1-4`, `d 1,3,7`, `d all`. See [Selecting several items](#selecting-several-items). |
| `t SEL` | Move one or **several** items to the Drive trash (after confirmation). Same selection syntax as `d`. |
| `u` | Upload files and/or folders into the current folder using the system file picker. |
| `m` | Create a new folder in the current folder. |
| `r` | Reload the current listing. |
| `x` | Log out and delete the saved token for this account from this computer. |
| `q` | Quit. |
| `Ctrl+C` | Cancel the current transfer (partial files are cleaned up). |

Notes:

- `u` and `m` only work **inside a folder**, not inside search results or "Shared with me". Enter a folder first.
- After an upload, folder creation or moving items to the trash, the list is refreshed automatically.

---

## Selecting several items

The `d` (download) and `t` (move to trash) commands accept **one or several items** at once. Write the command followed by the numbers shown in the `#` column:

| You type | It selects |
| --- | --- |
| `d 3` | Item 3. |
| `d 1-4` | Items 1, 2, 3 and 4. |
| `d 1,3,7` | Items 1, 3 and 7. |
| `d 2-5 9` | Items 2 to 5, and 9. Commas and spaces both work, and you can mix ranges and single numbers. |
| `d all` | **Every** item in the current listing (all pages, not just the one on screen). |

The same syntax works with `t`. Invalid input (`d 0`, `t 99`, `d abc`...) is rejected with a message and **nothing is done**. Typing just `d` or `t` shows a short reminder of the syntax.

---

## Working with files

Type the number of a file to open its menu:

```
File    : report.pdf
Type    : application/pdf
Size    : 2.4 MB

  1) View     2) Download     3) Information
  4) Move to trash                 0) Back
```

### 1) View

- **Text files** (plain text, source code, logs, JSON, CSV, Markdown, and many more) are shown in a pager. Only the first **1 MiB** is loaded; if the file is larger, a notice tells you to download it for the full content.
- **Google Docs and Slides** are exported as plain text and shown in the pager.
- **Google Sheets** are exported as CSV and shown in the pager (**first sheet only**).
- **Google Drawings** are exported to PNG and opened with your system's image viewer.
- **Any other file** (images, PDFs, videos, archives, and so on) is downloaded to a temporary folder and opened with the **system default application** (`os.startfile` on Windows, `open` on macOS, `xdg-open` on Linux). For files larger than **100 MB** the program asks for confirmation first.

The pager shows one screenful at a time: press **Enter** to continue or **q** to stop.

### 2) Download

Asks for a destination folder (default: your `Downloads` folder), then saves the file. For Google-native files you can choose the export format.

### 3) Information

Shows metadata: ID, name, MIME type, size, creation and modification times, web link and owners.

### 4) Move to trash

After confirmation (`y`), moves the file to the **Drive trash**. This is **not** a permanent deletion: you can restore the file from the trash in Google Drive. To trash several items at once, use `t` on the main screen (see [Moving to trash](#moving-to-trash)).

---

## Downloading

Use `d SEL` on the main screen (one or several items, see [Selecting several items](#selecting-several-items)), or the **Download** option in a file's menu.

### Destination

You are prompted for a destination folder. Press Enter to use the default (`~/Downloads`, or the current directory if it does not exist), or type `?` to pick the folder with the system dialog.

### Name collisions

Driv_term **never overwrites** existing files. If `report.pdf` already exists, the new file is saved as `report (1).pdf`, then `report (2).pdf`, and so on. Invalid filename characters (`< > : " / \ | ? *`) are replaced with `_`, which also protects against path traversal.

### Large files

Files of **32 MiB or more** are split into **16 MiB parts** that are downloaded in parallel and written into the right position of a temporary `.part` file. When all parts are finished, the file is renamed to its final name. If anything fails or you cancel, the `.part` file is removed so you never end up with a corrupted file that looks complete.

### Whole folders

`d 3` on a folder downloads it **recursively**:

1. The structure is read level by level, listing up to 30 folders per API query and running queries in parallel.
2. Local folders are created to mirror the Drive structure.
3. All files are downloaded in parallel (largest first).

Things to know:

- **Shortcuts** inside folders are **skipped** (this avoids infinite loops and duplicated data).
- Native Google files inside the folder are exported using the **first** format of each type (see the table below).
- A summary is shown at the end: number of files, number of errors and the reason for the first failure.

### Several files and folders at once

`d` accepts a selection (see [Selecting several items](#selecting-several-items)), so you can mix files and folders in a single command:

```
> d 1-3,6
Destination folder [C:\Users\you\Downloads]  (Enter = that one, ? = open the picker):
  Reading structure... 142 files.
  Downloading 142/142 files  1.2 GB / 1.2 GB  100%  38.4 MB/s
  Finished in 00:31 (average 38.1 MB/s)
```

- Everything goes into **one batch**: one progress bar and one shared thread pool, so small files from different folders do not wait for each other.
- Name collisions are resolved across the **whole selection** (two items called `report.pdf` become `report.pdf` and `report (1).pdf`), and existing files are never overwritten.
- Each selected folder is downloaded recursively, as described above. Native Google files are exported to the first format of their type.
- A selected **shortcut** is followed and its target is downloaded.
- At the destination prompt you can type `?` to open the system folder picker instead of typing a path.
- When it finishes you get a summary (`Download finished in <folder>: N files`) with the number of errors and the reason for the first failure, if any.

---

## Uploading

Press `u` inside a folder. Driv_term opens an upload screen where you build a list of local **files and folders** (any mix, as many as you want) and then uploads the whole list in one go:

```
Upload to: My Drive / Projects

Selected (3):
   DIR   C:\Users\you\Photos
   FILE  C:\Users\you\report.pdf
   FILE  C:\Users\you\notes.txt

  1) Choose files (several at once)      2) Choose folder(s) (repeat to add more)
  3) Type / paste paths                  c) Clear the list
  s) UPLOAD the selection                0) Cancel

>
```

| Key | Action |
| --- | --- |
| `1` | Opens the system **file picker**. Select one or several files at once. |
| `2` | Opens the system **folder picker**. See the table below for how many folders you can pick per dialog; you can always repeat the option to add more. |
| `3` | Type or paste paths by hand (one per line, empty line to finish). Dragging a file or folder onto the terminal pastes its path. |
| `c` | Clears the list. |
| `s` | Starts the upload of everything in the list. |
| `0` | Cancels and goes back to the browser without uploading anything. |

You can use `1`, `2` and `3` as many times as you like before pressing `s`. The list shows what is selected so far.

> The upload is only possible **inside a folder** (not in search results or "Shared with me"). Enter the destination folder first; its path is shown at the top of the upload screen.

### The local file picker

The picker is a **convenience, not a requirement**: Driv_term chooses the best option available on your computer.

| System | What is used | Several folders in one dialog |
| --- | --- | --- |
| Windows | Native Windows dialog (included with Python for Windows) | No, one folder per dialog (repeat `2`) |
| macOS | Native macOS dialog | Yes |
| Linux with a desktop | `zenity` if it is installed, otherwise `python3-tk` | Yes with `zenity`; one per dialog with `python3-tk` |
| Linux without a desktop, SSH, servers | No picker: typed-path mode | You type as many paths as you want |

On Linux you can install the graphical picker with `sudo apt install zenity` (or `sudo apt install python3-tk`).

### Without a graphical interface (CLI only)

If no picker can be opened (SSH session, server without a screen, no `zenity`/`tkinter`), Driv_term **detects it automatically** and falls back to typed paths. Pressing `1` or `2` prints a short notice and asks for the paths one per line:

```
  No graphical picker available (SSH or no display).
  On Linux you can install it with: sudo apt install zenity   (or python3-tk)
  Type or drag each path here (one per line). Empty line to finish.
  > /home/you/backup.tar
  > /home/you/photos
  >
```

Everything else (the list, `s` to upload, `c`, `0`) works exactly the same, so the experience is the same in a terminal-only environment.

> Signing in still needs a web browser on the same computer the first time (see [Signing in](#signing-in-oauth-flow)). On a headless server, authorize from a machine with a browser or use SSH port forwarding.

### What happens to the selection

- Duplicates are removed, and anything **already inside a selected folder is dropped**, so nothing is uploaded twice.
- Paths that do not exist are reported (`Does not exist: ...`) and ignored.
- Files and folders are uploaded in **one batch** with a single progress bar.

### Single files

- Files up to **5 MiB** are sent in **one** multipart request (metadata and content together), which halves the network round trips and is much faster for many small files.
- Larger files use Drive's **resumable upload**: the file is sent in **16 MiB chunks**. If the connection drops or the server returns a transient error, the program asks Drive how many bytes it already has and **resumes from there**, with up to 6 retries and growing delays.

### Folders

For every selected folder, Driv_term first creates the remote folder tree (level by level, in parallel) and then uploads all the files simultaneously (largest first). Unreadable items are skipped and reported in the final summary ("Skipped (no permission/unreadable)").

### Result summary

```
Upload finished: 128 files, 2 with errors
   Failed: a.bin, b.iso
   Reason for the first one: [403] ...
```

---

## Moving to trash

There are two ways to delete, both of which move items to the **Drive trash** (nothing is deleted permanently):

- **One file:** open its menu and choose `4) Move to trash`.
- **Several files and/or folders:** use `t` with a selection on the main screen.

```
> t 2,4-6
Move to trash (recoverable) (4):
   - Old backups/
   - draft.docx
   - photo1.jpg
   - photo2.jpg
Confirm [y/N]: y
  Moving to trash 4/4
Moved to trash: 4
```

How it works:

- It lists what is about to be trashed (up to 10 names; folders end with `/`) and asks for confirmation. **Any answer other than `y` cancels** and nothing is touched.
- Items are processed in parallel, with a live counter.
- Trashing a **folder** also trashes everything inside it.
- Items stay in the Drive trash, where you can restore them from Google Drive (Google keeps trashed items for about 30 days before removing them for good).
- If you select a **shortcut**, only the shortcut is trashed, **never** the file or folder it points to.
- If some items fail (for example, files shared with you that you do not own), the rest are still processed and the summary shows which ones failed and why.
- `t all` trashes **everything** in the current listing. Check the confirmation list before answering `y`.

---

## Google Docs, Sheets and Slides

Native Google files have no real size and cannot be downloaded as-is, so they are **exported**. When downloading a single file you choose the format. When downloading a **folder**, the first format in each list is used.

| Google file type | Available export formats (first = default for folders) |
| --- | --- |
| Document | `docx`, `pdf`, `txt` |
| Spreadsheet | `xlsx`, `csv`, `pdf` |
| Presentation | `pptx`, `pdf`, `txt` |
| Drawing | `png`, `pdf` |
| Other Google types | `pdf` |

The correct extension is appended to the file name automatically. Note that Google limits the size of exported content (about 10 MB per export through the API).

---

## Performance tuning

The number of simultaneous transfers is controlled by the `DRIVE_WORKERS` environment variable (default **8**, allowed range **1 to 32**). It applies to downloads, uploads and moving items to the trash.

**Linux / macOS**

```bash
DRIVE_WORKERS=12 python3 Driv_term_en.py
```

**Windows PowerShell**

```powershell
$env:DRIVE_WORKERS=12; python Driv_term_en.py
```

**Windows cmd**

```bat
set DRIVE_WORKERS=12
Driv_term_en.exe
```

Recommendations:

- Many small files: try **12 to 16** threads.
- A few huge files: the default is already good thanks to parallel parts.
- If you see many `429` / rate limit retries, **lower** the number. Google may throttle excessive parallelism.

The program prints the active number of threads at startup.

---

## Where your data is stored

Everything lives in a hidden folder in your home directory:

| File | Contents |
| --- | --- |
| `~/.drive_terminal/config.json` | Your OAuth `client_id` and `client_secret`. |
| `~/.drive_terminal/tokens.json` | The refresh token for each account you signed in with. |

On Linux and macOS these files are created with permissions **`600`** (readable and writable only by you). On Windows, `~` is your user profile (`C:\Users\<you>`).

Downloaded files go where you choose. Files opened with **View** (non-text) go to a temporary folder named `drive_term_*` in your system's temp directory.

---

## Security and privacy

- **No password handling.** Authentication happens in your browser with Google. The program only receives an authorization code on a local `127.0.0.1` address.
- **PKCE and `state` validation** protect the OAuth flow.
- **Your own credentials.** Nothing is sent to any server other than Google's. There is no telemetry, no analytics and no third-party backend.
- **Redirect safety.** The HTTP layer only follows redirects to Google domains (`*.googleapis.com`, `*.googleusercontent.com`, `*.google.com`) and refuses anything else.
- **Full Drive scope.** The app requests `https://www.googleapis.com/auth/drive`, which gives it read/write access to your Drive. This is needed to browse everything, upload and trash files. You can revoke it at any time at <https://myaccount.google.com/permissions>.
- **Protect your token file.** Anyone who can read `tokens.json` together with `config.json` can access your Drive. Do not share or commit the `~/.drive_terminal` folder.
- **Log out** with `x` to delete the saved token for the account.
- **Trash is reversible.** The program never permanently deletes files.

---

## Command-line options

| Option | Description |
| --- | --- |
| `--reset-config` | Deletes the saved OAuth credentials and tokens (`config.json` and `tokens.json`) and exits. Use it to switch to a different OAuth client or to wipe all local credentials. |

---

## How it works internally

This section is for the curious and for contributors.

**Architecture**

| Component | Responsibility |
| --- | --- |
| `Auth` | OAuth 2.0 loopback + PKCE login, token refresh (thread-safe), token storage. |
| `Http` | HTTPS layer with one persistent connection **per thread and host**, automatic retries with exponential backoff and jitter, 401 token refresh, safe redirect handling. |
| `Drive` | Drive API v3 calls: listing, search, batch listing, downloads (single, folder and multi-selection batch), exports, uploads (files and folders in one batch), folder creation and moving to trash. |
| `FileJob` | One file to download, which may consist of several parts. |
| `Progress` | A thread-safe global progress bar with smoothed speed and ETA. |
| `browse()` / `file_menu()` | The interactive terminal interface. |
| `pick_local()` / `choose_uploads()` | The local file picker (native dialog or typed-path fallback) and the upload selection screen. |
| `parse_selection()` | Parses selections such as `1-4,7` or `all` for `d` and `t`. |

**Networking details**

- Requests are retried (up to 6 times) on connection errors and on HTTP `429`, `500`, `502`, `503`, `504`, and on `403` rate-limit responses, with exponential backoff (max 20 s) plus random jitter.
- A `401` triggers one transparent access-token refresh and retry.
- Responses are requested with `Accept-Encoding: identity` so byte ranges and sizes are exact.
- Downloads of parts verify that the server honored the `Range` request; if it did not, the connection is reset and an error is raised instead of silently corrupting data.
- Exports verify `Content-Length` when present and retry if the download is incomplete.

**Download pipeline**

1. Pre-allocate a `.part` file of the final size.
2. Split into 16 MiB ranges (for files of 32 MiB or more).
3. Workers fetch ranges and write them at the correct offset (each worker has its own file handle).
4. When the last part of a file finishes, the `.part` file is atomically renamed (`os.replace`).
5. On cancellation or error, leftover `.part` files are deleted.

**Upload pipeline**

- Small: one `multipart/related` request with JSON metadata and file content.
- Large: start a resumable session, then `PUT` 16 MiB chunks with `Content-Range`. On failure, query the session (`Content-Range: bytes */size`) to learn the committed offset and continue from there.

**Listing**

- Folder contents use `orderBy=folder,name`, `pageSize=1000` and follow `nextPageToken`.
- Recursive downloads use queries like `('id1' in parents or 'id2' in parents ...)` in batches of 30 folders and map the results back to their parents.
- Shared Drives are supported through `supportsAllDrives` and `includeItemsFromAllDrives`.

---

## Limitations

- **Shortcuts are skipped** when downloading folders.
- Exporting Google-native files is subject to Google's export size limit (around 10 MB).
- The viewer shows at most the **first 1 MiB** of a text file and only the **first sheet** of a spreadsheet.
- No synchronization: Driv_term is an interactive browser and transfer tool, not a sync client.
- No rename, move, copy or permanent delete operations (only create folder, upload, download and move to trash). Moving to the trash is the only way to delete, and it is always reversible.
- On Windows (and Linux with `python3-tk`) the system dialog selects **one folder at a time**; repeat the option to add more. Several files, however, can be selected together.
- Items you do not own (for example some "Shared with me" files) cannot be moved to the trash; they are reported as errors while the rest of the selection is processed.
- Uploaded files are stored as-is: they are **not** converted into native Google Docs/Sheets/Slides.
- Name search matches names that *contain* the text; it does not search file contents.
- Transfers are not resumed across program restarts (resumption works only within a single run, for uploads).
- File integrity is not verified with checksums after transfer.

---

## Troubleshooting

**"Google hasn't verified this app" warning**
Expected for personal OAuth clients. Make sure your email is listed under **Test users** in the OAuth consent screen, then click *Advanced* and continue.

**`Error 403: access_denied`**
Your Google account is not in the **Test users** list of your OAuth consent screen. Add it and try again.

**I have to authorize again every week**
While an OAuth consent screen is in **Testing** status, Google expires refresh tokens after about 7 days. You can simply authorize again, or publish your app in the consent screen settings to avoid this.

**"The saved session has expired; you need to authorize again."**
The refresh token was revoked or expired. Authorize again when the browser opens. Use `--reset-config` if you want to start completely fresh.

**The browser did not open / I am on a remote server (SSH)**
Open the printed link in a browser **on the same computer where the program runs**, because the redirect goes to `127.0.0.1` on that machine. On a headless server, use SSH port forwarding or run the app on a machine with a browser.

**`Timed out.` during authorization**
You have 5 minutes to complete the sign-in. Run the program again.

**`[403] ... Drive API has not been used in project ...`**
You forgot to enable the **Google Drive API** in your Cloud project. Enable it and wait a minute.

**`[429]` / rate limit messages or slow transfers**
Reduce `DRIVE_WORKERS` (try 4). The program retries automatically with backoff.

**`Download interrupted` / `Connection closed by the server.`**
Temporary network problem. The program already retries several times; run the transfer again if it still fails.

**Garbled characters in the terminal**
Use a terminal with UTF-8 support (Windows Terminal is recommended on Windows). The program replaces unprintable characters instead of crashing.

**Screen looks broken on old Windows consoles**
Use Windows Terminal or PowerShell on a recent Windows version. The program enables ANSI support automatically on Windows.

**Windows SmartScreen / antivirus flags the `.exe`**
Unsigned executables often trigger warnings. Run the Python source instead, which you can read and verify.

**The file/folder picker does not open**
This happens over SSH, on servers without a screen, or on Linux without `zenity` or `python3-tk`. Driv_term then asks you to type the paths (one per line), so you can still upload. To get the graphical picker on Linux, install it with `sudo apt install zenity` (or `python3-tk`).

**`Number out of range` / `Invalid selection`**
The numbers after `d` or `t` must be in the `#` column of the current listing. Valid examples: `d 3`, `d 1-4`, `t 1,3,7`, `d all`. Nothing is downloaded or trashed when the selection is invalid.

**Some items could not be moved to the trash**
The summary lists the ones that failed and the reason of the first one. The usual cause is `[403]` on files you do not own (for example shared with you). The rest of the selection is still processed.

---

## FAQ

**Is this an official Google product?**
No. It is an independent open-source tool that uses the public Google Drive API.

**Do I need to pay for anything?**
No. Creating a Google Cloud project and OAuth credentials for personal use is free.

**Can I use multiple Google accounts?**
Yes. Enter a different email at startup. Tokens are stored per account. Use `x` to log out of one.

**Can I see Shared Drives?**
Items from Shared Drives are included in listings and searches. Use `c` for files shared directly with you.

**Does it delete my files?**
Only if you explicitly choose *Move to trash* (from a file's menu, or with `t` for several items), after a confirmation, and even then the files can be restored from the Drive trash. It never deletes permanently.

**Can I download or delete more than one file or folder at once?**
Yes. Use a selection: `d 1-3,5` to download, `t 2,4-6` to move to the trash, or `all` for everything in the listing. Files and folders can be mixed. See [Selecting several items](#selecting-several-items).

**Can I upload several files and folders at once?**
Yes. Press `u`, choose files and folders with the picker as many times as you want, and press `s` to upload them all in one batch.

**Does it work without a graphical interface (SSH, servers, Linux console)?**
Yes. The picker is optional: if no dialog can be opened, Driv_term asks you to type or paste the paths. Everything else is plain terminal. Only the first sign-in needs a browser on the same computer.

**Where are the temporary files?**
Non-text files opened with *View* are saved in a `drive_term_*` folder in your system temp directory.

**How do I completely remove everything?**
Run with `--reset-config`, delete the `~/.drive_terminal` folder, and revoke access at <https://myaccount.google.com/permissions>.

---

## Contributing

Issues and pull requests are welcome. If you find a bug, please include your operating system, Python version (or which `.exe` you used), the exact error message and the steps to reproduce it. Please **never** paste your `client_secret`, tokens or private file names in public issues.

## License

No license has been specified. All rights are reserved by the author. This is a free project with no money beneficts
