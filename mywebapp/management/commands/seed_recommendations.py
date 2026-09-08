from django.core.management.base import BaseCommand
from mywebapp.models import Recommendation


class Command(BaseCommand):
    help = "เพิ่มคำแนะนำเริ่มต้นสำหรับผล Stroke และ Non-Stroke"

    def handle(self, *args, **options):
        Recommendation.objects.update_or_create(
            result_type="STROKE",
            defaults={
                "content": (
                    "เตรียมเครื่องมือและทีมให้พร้อมสำหรับการรักษาเบื้องต้นโดยทันที "
                    "แจ้งแพทย์/พยาบาลเวร เตรียมอุปกรณ์ช่วยชีวิตและการตรวจวินิจฉัยฉุกเฉิน "
                    "(เช่น CT scan) และติดตามสัญญาณชีพอย่างใกล้ชิด"
                ),
            },
        )
        Recommendation.objects.update_or_create(
            result_type="NON_STROKE",
            defaults={
                "content": (
                    "เฝ้าสังเกตอาการต่อเนื่อง บันทึกสัญญาณชีพเป็นระยะ "
                    "และประเมินซ้ำหากมีอาการเปลี่ยนแปลงหรือมีอาการ FAST เกิดขึ้นใหม่"
                ),
            },
        )
        self.stdout.write(self.style.SUCCESS("เพิ่มคำแนะนำเริ่มต้นเรียบร้อยแล้ว"))
