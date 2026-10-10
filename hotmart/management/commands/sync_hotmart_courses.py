from django.core.management.base import BaseCommand, CommandError
from hotmart.client import HotmartError
from hotmart.services import sync_courses


class Command(BaseCommand):
    help = "Sincroniza cursos e ofertas da Hotmart preservando a apresentação local."

    def handle(self, *args, **options):
        try:
            count = sync_courses()
        except HotmartError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(self.style.SUCCESS(f"{count} cursos sincronizados."))
