from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Pnt2d
from OCC.Core.TopoDS import TopoDS_Vertex
from OCC.Core.BRep import BRep_Tool

from occwl.entity import Entity

class Vertex(Entity):
    """
    A topological vertex in a solid model
    Represents a 3D geometric point
    """
    def __init__(self, topods_vertex):
        """
        Constructor to initialize a vertex from a TodoDS_Vertex

        Args:
            topods_vertex (OCC.Core.TopoDS.TopoDS_Vertex): OCC Vertex
        """
        assert isinstance(topods_vertex, TopoDS_Vertex)
        self._vertex = topods_vertex

    def topods_entity(self):
        """
        Get the underlying OCC vertex as an entity

        Returns:
            OCC.Core.TopoDS.TopoDS_Vertex: Vertex
        """
        return self._vertex

    def __hash__(self):
        """
        Hash for the vertex

        Returns:
            int: Hash value
        """
        return self.topods_vertex().__hash__()
    
    def __eq__(self, other):
        """
        Equality check for the vertex
        """
        return self.topods_vertex().__hash__() == other.topods_vertex().__hash__()

    def point(self):
        """
        3D point stored in this vertex

        Returns:
            np.ndarray: 3D Point
        """
        pt = BRep_Tool.Pnt(self.topods_vertex())
        return (pt.X(), pt.Y(), pt.Z())

    def topods_vertex(self):
        """
        Get the underlying OCC vertex type

        Returns:
            OCC.Core.TopoDS.TopoDS_Vertex: Vertex
        """
        return self._vertex
