def classFactory(iface):
    from .plugin import ArchaeoTerrainExplorerPlugin
    return ArchaeoTerrainExplorerPlugin(iface)