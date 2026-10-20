# Workwise Job Portal

Workwise is a Django job portal where employers can publish and manage job
listings, and job seekers can search for roles, apply with a PDF resume, and
review their applications.

## Features

- Browse, search, and filter jobs by keyword and location.
- Paginated job listings with job details and annual salary in Indian rupees.
- Employer accounts can create, update, and delete their own job listings.
- Employers can see applicants for their listings and download their resumes.
- Job seekers can apply to a job once, using a PDF resume up to 10 MB.
- Applicants can see their application history and download their submitted
  resumes.
- Signup requires an email address and rejects addresses already used by
  another account, ignoring case.
- Login-required pages and role-specific actions.

## Requirements

- Python 3.12 or later
- Django 6.1.2

The project does not currently include a dependency manifest. Install Django
into your environment with:

```bash
python -m pip install Django==6.1.2
```

## Run locally

From the project root (the directory containing `manage.py`):

```bash
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The root URL redirects to the job listings at
`/jobs/`.

To create an administrator account for `/admin/`:

```bash
python manage.py createsuperuser
```

## Main URLs

| URL | Purpose |
| --- | --- |
| `/jobs/` | Browse and search job listings |
| `/jobs/<id>/` | View a job and apply |
| `/jobs/create/` | Create a job listing (employers) |
| `/jobs/mine/` | Manage your listings (employers) |
| `/jobs/<id>/applicants/` | Review applicants (the listing's employer) |
| `/jobs/applications/` | View your applications (job seekers) |
| `/jobs/applications/<id>/resume/` | Download a resume (the applicant or listing's employer) |
| `/jobs/<id>/update/` | Edit your job listing |
| `/jobs/<id>/delete/` | Delete your job listing |
| `/accounts/signup/` | Create an account |
| `/accounts/login/` | Sign in |
| `/accounts/logout/` | Sign out |
| `/admin/` | Django administration |

Job search accepts `q` for a keyword and `location` for a location filter, for
example:

```text
/jobs/?q=developer&location=Pune
```

## Accounts and permissions

During signup, choose either **Job Seeker** or **Employer**. Employers can
manage only jobs they posted. Job seekers can apply to jobs posted by other
users; each application must include a PDF resume.

Email addresses are checked case-insensitively during signup. This check is
implemented in the signup form; changes made directly through the database or
other account-creation paths do not currently have a database-level unique
email constraint.

## Tests and project checks

Run the Django test suite and configuration checks with:

```bash
python manage.py test
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Project layout

```text
accounts/       Custom user model, signup form and view
jobs/           Job/application models, views, routes, templates and styles
job_portal/     Django project settings and root URL configuration
manage.py       Django management command
db.sqlite3      Local SQLite database
```

## Production configuration

The checked-in settings are for local development. Before deployment, set a
private `SECRET_KEY`, disable `DEBUG`, configure `ALLOWED_HOSTS`, use a
production-ready database and email backend, and configure persistent media
storage for uploaded resumes. Protect resume downloads with the application's
authenticated routes rather than exposing the upload directory as public
static files.
