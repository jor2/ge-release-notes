import datetime
import os
import re

import markdown
from dateutil.tz import tzutc
from github import Github, Auth
from dotenv import load_dotenv

from html_template import html

load_dotenv()


class ReleaseNotesAutomator:
    def __init__(
            self,
            auth_token,
            repo_to_update,
            start_date,
            end_date,
            github_endpoint,
            org,
            local_run=True
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.github_endpoint = github_endpoint
        self.github_endpoint_api = f"https://{self.github_endpoint}/api/v3"
        self.org = org
        self.repo_to_update = repo_to_update
        self.local_run = local_run
        if self.local_run:
            self.html = html

        self.notes = "| Module | Version | Release Date | Details |  \n|---|---|---|---|  \n"

        auth = Auth.Token(auth_token)
        self.github_connection = Github(auth=auth)

        self.build_notes()
        self.push_commit()

        self.github_connection.close()

    def get_start_date(self):
        if self.start_date:
            return datetime.datetime.strptime(self.start_date, '%d-%m-%Y').replace(tzinfo=tzutc())
        return self.first_day_of_the_month_datetime

    def get_end_date(self):
        if self.end_date:
            return datetime.datetime.strptime(self.end_date, '%d-%m-%Y').replace(tzinfo=tzutc())
        return datetime.date.today()

    @property
    def repos(self):
        return [
            repo
            for repo in self.github_connection.get_user(self.org).get_repos()
            if "core-team" in repo.topics
        ]

    def get_releases_for_repo(self, repo):
        return [
            release
            for release in repo.get_releases()
            if self.get_start_date() <= release.created_at <= self.get_end_date()
            and "**deps:**" not in release.body
        ]

    def get_relevant_releases(self):
        relevant_releases = []
        for repo in self.repos:
            releases = self.get_releases_for_repo(repo)
            if len(releases) > 0:
                for release in releases:
                    release.repo = repo.name
                relevant_releases.extend(releases)
        return self.sort_releases_by_date(relevant_releases)

    def build_notes(self):
        print(f"Building release notes for start date: {self.get_start_date().strftime('%d-%m-%Y')} "
              f"- end date: {self.get_end_date().strftime('%d-%m-%Y')}...")
        rows = []
        for release in self.get_relevant_releases():
            html_body = self.get_html_from_markdown(release.body.strip())
            if self.local_run:
                rows.append(f"""
                <tr>
                  <td><a href="https://{self.github_endpoint}/{self.org}/{release.repo}">{release.repo}</a></td>
                  <td><a href="{self.release_url(release.repo, release.tag_name)}">{release.tag_name}</a></td>
                  <td>{release.created_at.strftime('%d-%m-%Y %H:%M')}</td>
                  <td>{html_body}</td>
                </tr>""")
            else:
                self.notes += f"| `{release.repo}` " \
                              f"| [{release.tag_name}]({self.release_url(release.repo, release.tag_name)}) " \
                              f"| {release.created_at.strftime('%d-%m-%Y %H:%M')} | {html_body} |  \n"
        self.html = self.html.format(content='\n'.join(rows))

    def get_html_from_markdown(self, body):
        md_body = ''
        if body not in [None, '']:
            md_body = markdown.markdown(self.pre_markdown_body(body))
            md_body = ' '.join(md_body.split())
        return md_body

    def release_url(self, repo, tag):
        return f"https://{self.github_endpoint}/{self.org}/{repo}/releases/tag/{tag}"

    def push_commit(self):
        repo = self.github_connection.get_repo(self.repo_to_update)
        file = repo.get_contents("README.md")
        if not self.local_run:
            repo.update_file(
                "README.md",
                f"docs: start date: {self.get_start_date().strftime('%d-%m-%Y')}"
                f" - end date: {self.get_end_date().strftime('%d-%m-%Y')}",
                self.notes,
                file.sha
            )
            print(f"Pushed commit to https://{self.github_endpoint}/{self.repo_to_update}")
        else:
            with open('README.md', 'w') as f:
                f.write(self.notes)
            with open('README.html', 'w') as f:
                f.write(self.html)

    @staticmethod
    def first_day_of_the_month_datetime():
        return datetime.datetime.combine(datetime.date.today(), datetime.time.min, tzinfo=tzutc()).replace(day=1)

    @staticmethod
    def pre_markdown_body(release_body):
        try:
            match = re.search(r'[(]\d{4}-\d{2}-\d{2}.\s*', release_body)
            return release_body.split(match.group())[-1].strip()
        except AttributeError:
            return release_body

    @staticmethod
    def sort_releases_by_date(releases):
        return sorted(releases, key=lambda release: release.created_at, reverse=True)


ReleaseNotesAutomator(
    auth_token=os.getenv("GH_TOKEN"),
    repo_to_update="jor2/ge-release-notes",
    start_date='19-10-2023',
    end_date='07-11-2023',
    github_endpoint="github.com",
    org="terraform-ibm-modules"
)
