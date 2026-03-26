# -*- coding: utf-8 -*-
"""
PyArchInit Installer Plugin
A QGIS plugin to install and update PyArchInit from GitHub
"""


def classFactory(iface):
    """Load PyArchInitInstaller class from file pyarchinit_installer.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .pyarchinit_installer import PyArchInitInstaller
    return PyArchInitInstaller(iface)
