from django.db import models
from django.utils.translation import gettext_lazy as _


class Provincia(models.Model):
    """Província de Moçambique"""
    nome = models.CharField(_("Nome da Província"), max_length=100, unique=True)
    latitude = models.FloatField(_("Latitude"), null=True, blank=True)
    longitude = models.FloatField(_("Longitude"), null=True, blank=True)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = _("Província")
        verbose_name_plural = _("Províncias")
        ordering = ['nome']


class Distrito(models.Model):
    """Distrito de Moçambique"""
    provincia = models.ForeignKey(
        Provincia,
        on_delete=models.CASCADE,
        related_name='distritos',
        verbose_name=_("Província")
    )
    nome = models.CharField(_("Nome do Distrito"), max_length=100)
    
    def __str__(self):
        return f"{self.nome} ({self.provincia.nome})"
    
    class Meta:
        verbose_name = _("Distrito")
        verbose_name_plural = _("Distritos")
        unique_together = ('provincia', 'nome')
        ordering = ['provincia__nome', 'nome']
