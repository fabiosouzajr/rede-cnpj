<!-- 126b0d27-9def-4be4-9edb-d88de9f78806 da18f573-b773-4b7d-9961-8b287fcab42f -->
# TSE Election Data Web Scraper Implementation Plan

## Overview

Build a Python web scraper using BeautifulSoup (no API) that navigates the TSE open data portal (https://dadosabertos.tse.jus.br/dataset/?groups=candidatos), iterates through election years, and downloads all available files from the "Dados e recursos" section by clicking "Explorar" links, organizing them in a `dados-tse/{year}/` directory structure.

## Implementation Steps

### 1. Project Setup and Dependencies

- Create new script: `rede_cria_tabelas/dados_tse_baixa.py`
- Use existing dependencies from `requirements.txt` (BeautifulSoup4, requests, lxml)
- Add `tqdm` for progress bars (check if needs to be added to requirements.txt)
- Start with BeautifulSoup only; add Selenium later only if JavaScript navigation is required

### 2. HTML Structure Inspection (First Step)

- Create a test function to fetch and inspect the actual HTML structure
- Print key sections to identify correct CSS selectors
- Document findings for:
  - Election year links structure
  - "Dados e recursos" section location
  - "Explorar" button/element structure
  - Download URL extraction path

### 3. Core Scraper Functions

#### 3.1 Main Navigation Function

- Function: `get_election_years(base_url)`
  - Use `requests.get()` to fetch the main candidates page
  - Parse HTML with BeautifulSoup using 'lxml' parser
  - Locate dataset links (inspect `.dataset-heading a` or similar selectors)
  - Extract year from link text (e.g., "Candidatos - 2024" → extract "2024")
  - Build full URLs using `urllib.parse.urljoin()` (handle relative URLs)
  - Handle pagination by checking for "next page" links
  - Return list of tuples: `[(year, url), ...]` sorted by year (newest first)

#### 3.2 Year Page Parser

- Function: `get_resources_from_year(year_url, year)`
  - Use `requests.get()` to fetch the year-specific dataset page
  - Parse HTML with BeautifulSoup
  - Locate "Dados e recursos" section (search for heading/text containing this phrase)
  - Find all "Explorar" elements (could be `<i>`, `<a>`, or `<button>` with "Explorar" text)
  - For each "Explorar" element:
    - Extract href or data attribute to get resource detail page URL
    - Navigate to resource detail page (follow href)
    - On resource page, find the actual download link (could be direct file URL or download button)
    - Extract: filename, file format, file size (if available in HTML)
    - Build complete download URL
  - Return list of dictionaries: `[{'name': '...', 'url': '...', 'format': '...', 'size': '...'}, ...]`
  - Handle cases where "Explorar" opens a modal vs. navigates to new page

#### 3.3 Download Function with Progress

- Function: `download_file(url, output_path, show_progress=True)`
  - Use `requests` with `stream=True` for large files
  - Use `tqdm` for progress bar showing:
    - File name (in description)
    - Total size (auto-formatted by tqdm)
    - Download speed (MB/s, auto-calculated)
    - Percentage completed (auto-calculated)
    - ETA (estimated time remaining)
  - Handle resume capability for interrupted downloads (check file size, use Range header)
  - Return success/failure status and error message if failed

### 4. User Interaction Functions

#### 4.1 Year Selection

- Function: `prompt_year_selection(available_years)`
  - Display available election years in a numbered list
  - Options:
    - "all" or "a" - Download all years
    - "last N" or "l N" - Download last N years (user specifies N, e.g., "last 10")
    - Specific numbers - Select specific years from list (comma-separated, e.g., "1,3,5")
  - Validate user input
  - Return filtered list of (year, url) tuples to process

#### 4.2 File Conflict Handling

- Function: `handle_existing_file(filepath, global_skip_all=False, global_overwrite_all=False)`
  - Check if file exists
  - If global flags are set, return action immediately
  - If exists and no global flag, prompt user:
    - "s" - Skip this file
    - "o" - Overwrite this file
    - "sa" - Skip all existing files (set global flag)
    - "oa" - Overwrite all existing files (set global flag)
  - Return tuple: `(action, updated_global_skip, updated_global_overwrite)`
  - Actions: 'skip', 'overwrite'

### 5. Directory Management

- Function: `setup_directories(base_dir="dados-tse", year=None)`
  - Create base directory if doesn't exist
  - If year provided, create year subdirectory: `{base_dir}/{year}/`
  - Return full path to directory

### 6. Main Execution Flow

- Function: `main()`

  1. Initialize base URL: `https://dadosabertos.tse.jus.br`
  2. Setup base directory `dados-tse`
  3. Get all available election years from main page
  4. Prompt user for year selection
  5. Prompt user for file conflict handling preference (initial)
  6. Initialize counters: downloaded, skipped, failed
  7. For each selected year:

     - Create year directory
     - Get all resources from year page
     - Print: "Processing year {year}: {count} resources found"
     - For each resource:
       - Build output filepath
       - Check if file exists
       - Handle conflict per user preference
       - If downloading:
         - Download with progress feedback
         - Handle errors gracefully (retry logic, max 3 retries)
         - Update counters

  1. Print summary: total downloaded, skipped, failed
  2. If any failed, save list to `dados-tse/failed_downloads.txt`

### 7. Error Handling and Logging

- Implement retry logic for failed downloads (max 3 retries with exponential backoff)
- Log errors to console with timestamps using `time.asctime()`
- Continue processing other files if one fails
- Save failed downloads list for manual retry: `[(year, filename, url, error), ...]`
- Handle network timeouts, connection errors, HTTP errors
- Validate downloaded file size matches expected size (if available)

### 8. Testing Strategy

- Test with a single year first (e.g., 2024)
- Verify "Dados e recursos" section structure
- Test "Explorar" link extraction
- Verify download URLs are correct
- Test progress bar with large files
- Test file conflict handling
- Test year selection prompts

## File Structure

```
rede_cria_tabelas/
├── dados_tse_baixa.py  (new file)
└── dados-tse/          (created at runtime)
    ├── 2024/
    │   ├── file1.csv
    │   ├── file2.zip
    │   └── ...
    ├── 2022/
    ├── 2020/
    └── failed_downloads.txt (if any failures)
```

## Key Implementation Details

### HTML Parsing Strategy

- Use BeautifulSoup with 'lxml' parser (already in requirements)
- First inspect actual HTML structure by fetching pages
- Target CSS selectors (to be determined during implementation):
  - Election year links: inspect `.dataset-heading a` or similar patterns
  - Resources section: find section/div containing "Dados e recursos" text
  - Explore buttons: search for elements containing "Explorar" text (case-insensitive)
  - Download links: may need to follow "Explorar" → resource page → actual download URL
- Handle both relative and absolute URLs using `urllib.parse.urljoin(base_url, relative_url)`
- Add debug mode to print HTML snippets when selectors fail
- Use `find_all()` with text matching for "Explorar" and "Dados e recursos"

### Download Progress Display

- Format using tqdm: `filename.ext | 45.2MB | 2.1MB/s | 67% | 00:23 ETA`
- Update in real-time
- Show file name in tqdm description
- Auto-format size and speed by tqdm

### User Prompts

- Use `input()` for interactive prompts
- Provide clear options with examples
- Validate user input with retry on invalid input
- Allow cancellation (Ctrl+C handling with graceful exit)
- Show progress: "Processing year X/Y: file Z/W"

## Dependencies to Add

- `tqdm` (for progress bars) - check if already in requirements.txt, add if missing

## Implementation Order

1. Create basic script structure with imports
2. Create test function to inspect HTML structure of TSE pages
3. Implement `get_election_years()` function
4. Test year extraction with a few years
5. Implement `get_resources_from_year()` function
6. Test resource extraction for one year
7. Implement `download_file()` with progress bar
8. Test download with a small file
9. Implement user interaction functions
10. Implement main() function
11. Test end-to-end with one year
12. Test with multiple years and edge cases

## Notes

- Follow existing code style from `dados_cnpj_baixa.py` (similar structure, error handling)
- Use similar patterns: time.asctime() for logging, similar directory structure
- Consider adding parallel downloads option (like parfive) for future enhancement
- Handle rate limiting if server restricts requests (add delays between requests)
- Add User-Agent header to requests to avoid blocking
- Consider adding a config file for base URL and other settings