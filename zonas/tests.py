from django.test import TestCase
from django.urls import reverse
from .models import Departamento, Provincia, Distrito, Caserio


class ZonasApiTests(TestCase):
	def setUp(self):
		self.dep = Departamento.objects.create(nombre='Dep Test')
		self.prov = Provincia.objects.create(departamento=self.dep, nombre='Prov Test')
		self.dist = Distrito.objects.create(provincia=self.prov, nombre='Dist Test')
		self.cas = Caserio.objects.create(distrito=self.dist, nombre='Caserio Test', activa=True)

	def test_api_departamentos(self):
		url = reverse('api_departamentos')
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertIsInstance(data, list)
		self.assertTrue(any(d['nombre'] == 'Dep Test' for d in data))

	def test_api_provincias(self):
		url = reverse('api_provincias', args=[self.dep.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(any(p['nombre'] == 'Prov Test' for p in data))

	def test_api_distritos(self):
		url = reverse('api_distritos', args=[self.prov.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(any(d['nombre'] == 'Dist Test' for d in data))

	def test_api_caserios(self):
		url = reverse('api_caserios', args=[self.dist.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(any(c['nombre'] == 'Caserio Test' for c in data))
