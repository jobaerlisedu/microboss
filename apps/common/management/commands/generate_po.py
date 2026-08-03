from pathlib import Path
from django.core.management.base import BaseCommand

PO_CONTENT = r'''# Bengali translations for CMS project.
# Copyright (C) 2026 Channel One Digital
# This file is distributed under the same license as the Django CMS project.
#
msgid ""
msgstr ""
"Project-Id-Version: CMS 1.0\n"
"Report-Msgid-Bugs-To: admin@channelone.com\n"
"POT-Creation-Date: 2026-07-18 12:00+0600\n"
"PO-Revision-Date: 2026-07-18 12:00+0600\n"
"Last-Translator: CMS Team\n"
"Language-Team: Bengali\n"
"Language: bn\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"

#: apps/accounts/models.py
msgid "Nickname"
msgstr "Nickname"

msgid "Full Name"
msgstr "Full Name"

msgid "Office Id"
msgstr "Office Id"

msgid "Designation"
msgstr "Designation"

msgid "The Phone"
msgstr "The Phone"

msgid "Blood Group"
msgstr "Blood Group"

msgid "Date Of Birth"
msgstr "Date Of Birth"

msgid "Facebook Id"
msgstr "Facebook Id"

msgid "Admin"
msgstr "Admin"

msgid "The Founder"
msgstr "The Founder"

msgid "The User"
msgstr "The User"

msgid "Users"
msgstr "Users"

msgid "Session"
msgstr "Session"

msgid "Sessions"
msgstr "Sessions"

#: apps/content/models.py
msgid "The Date"
msgstr "The Date"

msgid "Time"
msgstr "Time"

msgid "Content Slug Name"
msgstr "Content Slug Name"

msgid "The Headline"
msgstr "The Headline"

msgid "The Uploader"
msgstr "The Uploader"

msgid "Links"
msgstr "Links"

msgid "Sponsor"
msgstr "Sponsor"

msgid "Comment"
msgstr "Comment"

msgid "Content Entry"
msgstr "Content Entry"

msgid "Content Entries"
msgstr "Content Entries"

#: apps/sponsors/models.py
msgid "Sponsor'S Name"
msgstr "Sponsor'S Name"

msgid "how many per day"
msgstr "how many per day"

msgid "how many in total"
msgstr "how many in total"

msgid "Start Date"
msgstr "Start Date"

msgid "Last Date"
msgstr "Last Date"

msgid "Content Type"
msgstr "Content Type"

msgid "Dougie (Ft)"
msgstr "Dougie (Ft)"

msgid "Popup X2"
msgstr "Popup X2"

msgid "Tvc X1"
msgstr "Tvc X1"

msgid "Gpi X1"
msgstr "Gpi X1"

msgid "Sponsors"
msgstr "Sponsors"

#: apps/accounts/serializers.py
msgid "The two passwords do not match"
msgstr "The two passwords do not match"

msgid "Already registered with this nickname/email/office id"
msgstr "Already registered with this nickname/email/office id"

#: apps/accounts/views.py
msgid "Incorrect Information Provided"
msgstr "Incorrect Information Provided"

msgid "Logged Out"
msgstr "Logged Out"

msgid "Password Reset"
msgstr "Password Reset"

msgid "OTP has been sent"
msgstr "OTP has been sent"

msgid "Code does not match"
msgstr "Code does not match"

msgid "The session has expired"
msgstr "The session has expired"

msgid "User Not Found"
msgstr "User Not Found"

msgid "Password must be at least 4 characters"
msgstr "Password must be at least 4 characters"

msgid "No one else can remove the founder from admin"
msgstr "No one else can remove the founder from admin"

msgid "Maximum 3 admins can be kept"
msgstr "Maximum 3 admins can be kept"

#: apps/core/permissions.py
msgid "You do not have permission to perform this action"
msgstr "You do not have permission to perform this action"

#: apps/content/serializers.py
msgid "At least 1 link is required"
msgstr "At least 1 link is required"

msgid "This headline is already listed"
msgstr "This headline is already listed"

#: apps/reports/pdf_utils.py
msgid "Content Report"
msgstr "Content Report"

#: templates
msgid "Channel One Digital — Content Management System"
msgstr "Channel One Digital — Content Management System"

msgid "Login"
msgstr "Login"

msgid "Register"
msgstr "Register"

msgid "Save"
msgstr "Save"

msgid "Cancel"
msgstr "Cancel"

msgid "Delete"
msgstr "Delete"

msgid "Pdf Download"
msgstr "Pdf Download"

msgid "No Entries Found"
msgstr "No Entries Found"

msgid "Channel One Digital — Content Log"
msgstr "Channel One Digital — Content Log"
'''


class Command(BaseCommand):
    help = 'Generate Bengali .po translation file manually'

    def handle(self, *args, **options):
        locale_dir = Path('locale') / 'bn' / 'LC_MESSAGES'
        locale_dir.mkdir(parents=True, exist_ok=True)
        po_file = locale_dir / 'django.po'
        po_file.write_text(PO_CONTENT, encoding='utf-8')
        self.stdout.write(self.style.SUCCESS(f'Created {po_file}'))
        self.stdout.write(f'Total msgid entries: {PO_CONTENT.count("msgid ")}')
