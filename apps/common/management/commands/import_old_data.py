import json
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from apps.accounts.models import User
from apps.content.models import ContentEntry
from apps.sponsors.models import Sponsor
from apps.contentlist.models import ContentListItem
from apps.assignments.models import Assignment
from apps.scripts.models import Script


class Command(BaseCommand):
    help = 'Import data from old CMS JSON export file'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the exported JSON file')

    def handle(self, *args, **options):
        filepath = options['json_file']
        self.stdout.write(f'Reading data from {filepath}...')

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Import users
        user_map = {}
        for u in data.get('users', []):
            user, created = User.objects.get_or_create(
                username=u.get('nickname', ''),
                defaults={
                    'full_name': u.get('fullName', ''),
                    'office_id': u.get('officeId', ''),
                    'designation': u.get('designation', ''),
                    'email': u.get('email', ''),
                    'phone': u.get('phone', ''),
                    'blood_group': u.get('bloodGroup', 'O+'),
                    'date_of_birth': u.get('dob', None),
                    'facebook_id': u.get('facebookId', ''),
                    'is_admin': u.get('isAdmin', False),
                    'is_founder': u.get('isFounder', False),
                    'password': make_password(u.get('passwordHash', 'default')),
                },
            )
            user_map[u['id']] = user
            self.stdout.write(f'  {"Created" if created else "Skipped"} user: {user.username}')

        # Import sponsors
        sponsor_map = {}
        for s in data.get('sponsors', []):
            creatives = s.get('creatives', {})
            sponsor, created = Sponsor.objects.get_or_create(
                name=s['name'],
                defaults={
                    'daily_quota': s.get('dailyQuota', 0),
                    'total_quota': s.get('totalQuota', 0),
                    'start_date': s.get('startDate'),
                    'end_date': s.get('endDate'),
                    'content_type': s.get('contentType', ''),
                    'has_doggy': creatives.get('doggy', False),
                    'has_popup': creatives.get('popup', False),
                    'has_tvc': creatives.get('tvc', False),
                    'has_gpi': creatives.get('gpi', False),
                },
            )
            sponsor_map[s['id']] = sponsor
            self.stdout.write(f'  {"Created" if created else "Skipped"} sponsor: {sponsor.name}')

        # Import content entries
        for e in data.get('entries', []):
            member = user_map.get(e.get('memberId'))
            sponsor = sponsor_map.get(e.get('sponsorId')) if e.get('sponsorId') else None
            if not member:
                self.stdout.write(f'  Skipping entry — member not found: {e.get("headline", "")[:40]}')
                continue
            ContentEntry.objects.create(
                entry_date=e.get('date'),
                entry_time=e.get('time', '00:00'),
                slug=e.get('slug', ''),
                headline=e.get('headline', ''),
                member=member,
                links=e.get('links', {}),
                sponsor=sponsor,
                comment=e.get('comment', ''),
            )
        self.stdout.write(f'  Imported {len(data.get("entries", []))} content entries')

        # Import content list items
        for cl in data.get('contentList', []):
            member = user_map.get(cl.get('memberId'))
            ContentListItem.objects.create(
                list_date=cl.get('date'),
                content=cl.get('content', ''),
                source=cl.get('source', 'social'),
                district=cl.get('district', ''),
                footage_source=cl.get('footage', ''),
                member=member or User.objects.first(),
            )
        self.stdout.write(f'  Imported {len(data.get("contentList", []))} content list items')

        # Import assignments
        for a in data.get('assignments', []):
            member = user_map.get(a.get('memberId'))
            Assignment.objects.create(
                assign_date=a.get('date'),
                caption=a.get('caption', ''),
                source_link=a.get('link', ''),
                district=a.get('district', ''),
                reporter=a.get('reporter', ''),
                status=a.get('status', 'Assigned'),
                member=member or User.objects.first(),
            )
        self.stdout.write(f'  Imported {len(data.get("assignments", []))} assignments')

        # Import scripts
        for s in data.get('scripts', []):
            writer = user_map.get(s.get('writerId'))
            Script.objects.create(
                script_date=s.get('date'),
                headline=s.get('headline', ''),
                source=s.get('source', 'social'),
                writer=writer or User.objects.first(),
                district=s.get('district', ''),
                district_reporter=s.get('districtReporter', ''),
                body=s.get('body', ''),
                status=s.get('status', 'draft'),
                approved_at=s.get('approvedAt'),
            )
        self.stdout.write(f'  Imported {len(data.get("scripts", []))} scripts')

        self.stdout.write(self.style.SUCCESS('Import complete!'))
