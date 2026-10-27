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
10. [Working with files](#working-with-files)
11. [Downloading](#downloading)
12. [Uploading](#uploading)
13. [Google Docs, Sheets and Slides](#google-docs-sheets-and-slides)
14. [Performance tuning](#performance-tuning)
15. [Where your data is stored](#where-your-data-is-stored)
16. [Security and privacy](#security-and-privacy)
17. [Command-line options](#command-line-options)
18. [How it works internally](#how-it-works-internally)
19. [Limitations](#limitations)
20. [Troubleshooting](#troubleshooting)
21. [FAQ](#faq)

---

## Features

- **Full Drive navigation** from the keyboard: folders, "Shared with me", and name search.
- **Parallel transfers.** Several files are downloaded or uploaded at the same time using a thread pool (8 threads by default, configurable).
- **Persistent HTTPS connections.** No new DNS lookup, TCP connection and TLS handshake for every request, which makes a big difference with many small files.
- **Chunked parallel downloads.** Large files are split into 16 MiB parts that are downloaded simultaneously with HTTP `Range` requests.
- **Fast recursive folder download.** The folder tree is listed in batches and in parallel instead of one request per folder.
- **Smart uploads.** Small files (up to 5 MiB) go in a single multipart request. Large files use Drive's resumable upload protocol with 16 MiB chunks and automatic recovery after network failures.
- **Whole-folder upload and download**, preserving the directory structure.
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
| `code/` | The Python source code of the application. |
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
python3 <script_name>.py
```

On Windows, use `python` instead of `python3`. Replace `<script_name>.py` with the actual script file inside the `code/` folder.

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
  d N download folder/file (e.g. d 3) | u upload | m new folder
  r reload | x log out | q quit   (Ctrl+C cancels a transfer)

>
```

**Columns**

| Column | Meaning |
| --- | --- |
| `#` | The number you type to open an item or to use with `d`. |
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
| `d N` | Download item number `N` (file or whole folder), e.g. `d 3`. |
| `u` | Upload a local file or folder into the current folder. |
| `m` | Create a new folder in the current folder. |
| `r` | Reload the current listing. |
| `x` | Log out and delete the saved token for this account from this computer. |
| `q` | Quit. |
| `Ctrl+C` | Cancel the current transfer (partial files are cleaned up). |

Notes:

- `u` and `m` only work **inside a folder**, not inside search results or "Shared with me". Enter a folder first.
- After an upload, folder creation or removal, the list is refreshed automatically.

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

After confirmation (`y`), moves the file to the **Drive trash**. This is **not** a permanent deletion: you can restore the file from the trash in Google Drive.

---

## Downloading

Use `d N` on the main screen, or the **Download** option in a file's menu.

### Destination

You are prompted for a destination folder. Press Enter to use the default (`~/Downloads`, or the current directory if it does not exist).

### Name collisions

Driv_term **never overwrites** existing files. If `report.pdf` already exists, the new file is saved as `report (1).pdf`, then `report (2).pdf`, and so on. Invalid filename characters (`< > : " / \ | ? *`) are replaced with `_`, which also protects against path traversal.

### Large files

Files of **32 MiB or more** are split into **16 MiB parts** that are downloaded in parallel and written into the right position of a temporary `.part` file. When all parts are finished, the file is renamed to its final name. If anything fails or you cancel, the `.part` file is removed so you never end up with a corrupted file that looks complete.

### Whole folders

`d N` on a folder downloads it **recursively**:

1. The structure is read level by level, listing up to 30 folders per API query and running queries in parallel.
2. Local folders are created to mirror the Drive structure.
3. All files are downloaded in parallel (largest first).

Things to know:

- **Shortcuts** inside folders are **skipped** (this avoids infinite loops and duplicated data).
- Native Google files inside the folder are exported using the **first** format of each type (see the table below).
- A summary is shown at the end: number of files, number of errors and the reason for the first failure.

---

## Uploading

Press `u` inside a folder and enter the local path of a **file or folder**. Quotes around the path and `~` are handled for you.

### Single files

- Files up to **5 MiB** are sent in **one** multipart request (metadata and content together), which halves the network round trips and is much faster for many small files.
- Larger files use Drive's **resumable upload**: the file is sent in **16 MiB chunks**. If the connection drops or the server returns a transient error, the program asks Drive how many bytes it already has and **resumes from there**, with up to 6 retries and growing delays.

### Folders

When you upload a folder, Driv_term first creates the remote folder tree (level by level, in parallel) and then uploads all the files simultaneously (largest first). Unreadable items are skipped and reported in the final summary ("Skipped (no permission/unreadable)").

### Result summary

```
Upload completed: 128 files, 2 with errors
   Failed: a.bin, b.iso
   Reason for the first one: [403] ...
```

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

The number of simultaneous transfers is controlled by the `DRIVE_WORKERS` environment variable (default **8**, allowed range **1 to 32**).

**Linux / macOS**

```bash
DRIVE_WORKERS=12 python3 <script_name>.py
```

**Windows PowerShell**

```powershell
$env:DRIVE_WORKERS=12; python <script_name>.py
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
| `Drive` | Drive API v3 calls: listing, search, batch listing, downloads, exports, uploads, folder creation. |
| `FileJob` | One file to download, which may consist of several parts. |
| `Progress` | A thread-safe global progress bar with smoothed speed and ETA. |
| `browse()` / `file_menu()` | The interactive terminal interface. |

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
- No rename, move, copy or permanent delete operations (only create folder, upload, download and move to trash).
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
Only if you explicitly choose *Move to trash*, and even then the files can be restored from the Drive trash.

**Where are the temporary files?**
Non-text files opened with *View* are saved in a `drive_term_*` folder in your system temp directory.

**How do I completely remove everything?**
Run with `--reset-config`, delete the `~/.drive_terminal` folder, and revoke access at <https://myaccount.google.com/permissions>.

---

## Contributing

Issues and pull requests are welcome. If you find a bug, please include your operating system, Python version (or which `.exe` you used), the exact error message and the steps to reproduce it. Please **never** paste your `client_secret`, tokens or private file names in public issues.

## License

No license has been specified. This is a free project I made for my personal use and uploaded here for everyone to use it freely. 
