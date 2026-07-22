from pathlib import Path
from django.core.management.base import BaseCommand

try:
    import polib
except ImportError:
    polib = None


class Command(BaseCommand):
    help = 'Compile .po translation files to .mo without GNU gettext'

    def handle(self, *args, **options):
        if polib is None:
            self.stdout.write(self.style.ERROR('polib not installed. Run: pip install polib'))
            return

        base_dir = Path('locale')
        compiled = 0
        for po_file in base_dir.rglob('*.po'):
            mo_file = po_file.with_suffix('.mo')
            try:
                po = polib.pofile(str(po_file))
                po.save_as_mofile(str(mo_file))
                self.stdout.write(self.style.SUCCESS(
                    f'Compiled: {po_file.relative_to(base_dir)} -> {mo_file.relative_to(base_dir)}'
                ))
                compiled += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f'Failed to compile {po_file.name}: {e}'
                ))

        self.stdout.write(self.style.SUCCESS(f'Compiled {compiled} .po file(s)'))
