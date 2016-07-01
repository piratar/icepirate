# -*- coding: utf-8 -*-
#
# This comment will populate certain fixed Icelandic tables with data
#
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from locationcode.models import LocationCode


# Gögn frá: https://is.wikipedia.org/wiki/%C3%8Dslensk_sveitarf%C3%A9l%C3%B6g_eftir_sveitarf%C3%A9lagsn%C3%BAmerum
SVEITARFELOG = (
    ('', '0000', 'Reykjavíkurborg', (101,102,103,104,105,107,108,109,110,111,112,113,116,121,123,124,125,127,128,129,130,132,150,155)),
    ('SV', '1000', 'Kópavogsbær', (200, 201, 202, 203)),
    ('SV', '1100', 'Seltjarnarnesbær', (170,)),
    ('SV', '1300', 'Garðabær', (210,)),
    ('SV', '1400', 'Hafnarfjarðarkaupstaður', (220,221,222)),
    ('SV', '1603', 'Sveitarfélagið Álftanes', (225,)),
    ('SV', '1604', 'Mosfellsbær', (270,)),
    ('SV', '1606', 'Kjósarhreppur', (270,)),
    ('S', '2000', 'Reykjanesbær', (230,232,233,235,260,)),
    ('S', '2300', 'Grindavíkurbær', (240,)),
    ('S', '2503', 'Sandgerðisbær', (245,)),
    ('S', '2504', 'Sveitarfélagið Garður', (250,)),
    ('S', '2506', 'Sveitarfélagið Vogar', (190,)),
    ('NV', '3000', 'Akraneskaupstaður', (300,)),
    ('NV', '3506', 'Skorradalshreppur', (311,)),
    ('NV', '3511', 'Hvalfjarðarsveit', (301,)),
    ('NV', '3609', 'Borgarbyggð', (310,311,320,)),
    ('NV', '3709', 'Grundarfjarðarbær', (350,)),
    ('NV', '3710', 'Helgafellssveit', (340,)),
    ('NV', '3711', 'Stykkishólmsbær', (340,)),
    ('NV', '3713', 'Eyja- og Miklaholtshreppur', (311,)),
    ('NV', '3714', 'Snæfellsbær', (360,)),
    ('NV', '3811', 'Dalabyggð', (370,371,)),
    ('NV', '4100', 'Bolungarvíkurkaupstaður', (415,)),
    ('NV', '4200', 'Ísafjarðarbær', (400,401,410,425,430,470,471,)),
    ('NV', '4502', 'Reykhólahreppur', (380,)),
    ('NV', '4604', 'Tálknafjarðarhreppur', (460,)),
    ('NV', '4607', 'Vesturbyggð', (450,451,465,)),
    ('NV', '4803', 'Súðavíkurhreppur', (420,)),
    ('NV', '4901', 'Árneshreppur', (524,)),
    ('NV', '4902', 'Kaldrananeshreppur', (510,520,)),
    ('NV', '4908', 'Bæjarhreppur', (500,)),
    ('NV', '4911', 'Strandabyggð', (510,)),
    ('NV', '5200', 'Sveitarfélagið Skagafjörður', (550,551,560,565,566,570,)),
    ('NV', '5508', 'Húnaþing vestra', (500,530,531,)),
    ('NV', '5604', 'Blönduósbær', (540,)),
    ('NV', '5609', 'Sveitarfélagið Skagaströnd', (545,)),
    ('NV', '5611', 'Skagabyggð', (545,)),
    ('NV', '5612', 'Húnavatnshreppur', (541,)),
    ('NV', '5706', 'Akrahreppur', (560,)),
    ('NA', '6000', 'Akureyrarkaupstaður', (600,603,611,630,)),
    ('NA', '6100', 'Norðurþing', (640,670,671,675,)),
    ('NA', '6250', 'Fjallabyggð', (580,625,)),
    ('NA', '6400', 'Dalvíkurbyggð', (620,621,)),
    ('NA', '6513', 'Eyjafjarðarsveit', (601,)),
    ('NA', '6515', 'Hörgársveit', (601,)),
    ('NA', '6601', 'Svalbarðsstrandarhreppur', (601,)),
    ('NA', '6602', 'Grýtubakkahreppur', (601,610,)),
    ('NA', '6607', 'Skútustaðahreppur', (660,)),
    ('NA', '6611', 'Tjörneshreppur', (641,)),
    ('NA', '6612', 'Þingeyjarsveit', (601,641,645,650,)),
    ('NA', '6706', 'Svalbarðshreppur', (681,)),
    ('NA', '6709', 'Langanesbyggð', (680,681,685,)),
    ('NA', '7000', 'Seyðisfjarðarkaupstaður', (710,)),
    ('NA', '7300', 'Fjarðabyggð', (715,730,735,740,750,755,)),
    ('NA', '7502', 'Vopnafjarðarhreppur', (690,)),
    ('NA', '7505', 'Fljótsdalshreppur', (701,)),
    ('NA', '7509', 'Borgarfjarðarhreppur', (701,)),
    ('NA', '7613', 'Breiðdalshreppur', (760,)),
    ('NA', '7617', 'Djúpavogshreppur', (765,)),
    ('NA', '7620', 'Fljótsdalshérað', (700,701,)),
    ('S', '7708', 'Sveitarfélagið Hornafjörður', (780,781,785,)),
    ('S', '8000', 'Vestmannaeyjabær', (900,902,)),
    ('S', '8200', 'Sveitarfélagið Árborg', (800,801,802,820,825,)),
    ('S', '8508', 'Mýrdalshreppur', (870,871,)),
    ('S', '8509', 'Skaftárhreppur', (880,)),
    ('S', '8610', 'Ásahreppur', (851,)),
    ('S', '8613', 'Rangárþing eystra', (860,861,)),
    ('S', '8614', 'Rangárþing ytra', (850,851,)),
    ('S', '8710', 'Hrunamannahreppur', (845,)),
    ('S', '8716', 'Hveragerðisbær', (810,)),
    ('S', '8717', 'Sveitarfélagið Ölfus', (815,)),
    ('S', '8719', 'Grímsnes- og Grafningshreppur', (801,)),
    ('S', '8720', 'Skeiða- og Gnúpverjahreppur', (801,)),
    ('S', '8721', 'Bláskógabyggð', (801,)),
    ('S', '8722', 'Flóahreppur', (801,)))

KJORDAEMIN = {
#   'RN': 'Reykjavíkurkjördæmi Norður',
#   'RS': 'Reykjavíkurkjördæmi Suður',
    'S': 'Suðurkjördæmi',
    'SV': 'Suðurvesturkjördæmi',
    'NV': 'Norðvesturkjördæmi',
    'NA': 'Norðausturkjördæmi'}


class Command(BaseCommand):

    def _add_or_update_code(self, code, name):
        try:
            lc = LocationCode(
                location_name=name,
                location_code=code)
            lc.save()
        except IntegrityError:
            lc = LocationCode.objects.get(location_code=code)
            if lc.location_name and lc.location_name != name:
                lc.location_name = name
            lc.save()
        return lc

    def handle(self, *args, **options):
        for kd in sorted(KJORDAEMIN.keys()):
            self._add_or_update_code('kd:%s' % kd, KJORDAEMIN[kd])

        postnumerin = {}
        for kd, svfnr, nafn, postnumer in SVEITARFELOG:
            for pnr in postnumer:
                pnr = '%3.3d' % pnr
                if pnr in postnumerin:
                    postnumerin[pnr] = '%s, %s' % (postnumerin[pnr], nafn)
                else:
                    postnumerin[pnr] = nafn

        for kd, svfnr, nafn, postnumer in SVEITARFELOG:
            slc = self._add_or_update_code('svfnr:' + svfnr, nafn)
            if kd:
                lc = LocationCode.objects.get(location_code='kd:%s' % kd)
                lc.auto_location_codes.add(slc)

        for pnr in sorted(postnumerin.keys()):
            self._add_or_update_code('pnr:' + pnr, postnumerin[pnr])
