import numpy as np

from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec, gp_Pnt2d
from OCC.Core.BRep import BRep_Tool_Curve, BRep_Tool_Continuity
from OCC.Core.GeomLProp import GeomLProp_SLProps
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GeomAbs import GeomAbs_Line, GeomAbs_Circle, GeomAbs_Ellipse, GeomAbs_Hyperbola, GeomAbs_Parabola, GeomAbs_BezierCurve, GeomAbs_BSplineCurve, GeomAbs_OffsetCurve, GeomAbs_OtherCurve
from OCC.Core.TopAbs import TopAbs_REVERSED
from OCC.Extend import TopologyUtils
from OCC.Core.TopoDS import TopoDS_Edge
from OCC.Core.GCPnts import GCPnts_AbscissaPoint
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.ShapeAnalysis import ShapeAnalysis_Edge

import occwl.geometry.geom_utils as geom_utils
from occwl.geometry.interval import Interval

class Edge:
    """
    A topological edge in a solid model
    Represents a 3D curve bounded by vertices
    """
    def __init__(self, topods_edge):
        assert isinstance(topods_edge, TopoDS_Edge)
        self._edge = topods_edge
    
    def topods_edge(self):
        """
        Get the underlying OCC edge type

        Returns:
            OCC.Core.TopoDS.TopoDS_Edge: Edge
        """
        return self._edge

    def hash(self):
        """
        Hash for the edge

        Returns:
            int: Hash value
        """
        return hash(self.topods_edge())
    
    def point(self, u):
        """
        Evaluate the edge geometry at given parameter

        Args:
            u (float): Curve parameter
        
        Returns:
            np.ndarray: 3D Point
        """
        if self.has_curve():
            pt = self.curve().Value(u)
            return geom_utils.gp_to_numpy(pt)
        # If the edge has no curve then return a point
        # at the origin.
        # It would ne nice to return the location of the 
        # vertex
        return np.array([0,0,0])

    def tangent(self, u):
        """
        Compute the tangent of the edge geometry at given parameter

        Args:
            u (float): Curve parameter

        Returns:
            np.ndarray: 3D unit vector
        """
        if self.has_curve():
            pt = gp_Pnt()
            der = gp_Vec()
            self.curve().D1(u, pt, der)
            der.Normalize()
            tangent = geom_utils.gp_to_numpy(der)
            if self.reversed():
                tangent = -tangent
            return tangent
        # If the edge has no curve then return 
        # a zero vector
        return np.array([0,0,0])
    
    def first_derivative(self, u):
        """
        Compute the first derivative of the edge geometry at given parameter

        Args:
            u (float): Curve parameter

        Returns:
            np.ndarray: 3D vector
        """
        if self.has_curve():
            pt = gp_Pnt()
            der = gp_Vec()
            self.curve().D1(u, pt, der)
            return geom_utils.gp_to_numpy(der)
        # If the edge has no curve then return 
        # a zero vector
        return np.array([0,0,0])

    def length(self, tolerance=1e-9):
        """
        Compute the length of the edge curve

        Args:
            tolerance (float, optional): Tolerance to compute abscissa points. Defaults to 1e-9.

        Returns:
            float: Length of the edge curve
        """
        if not self.has_curve():
            return 0.0
        bounds = self.u_bounds()
        return GCPnts_AbscissaPoint().Length(
            BRepAdaptor_Curve(self.topods_edge()), 
            bounds.a, 
            bounds.b, 
            tolerance
        )

    def curve(self):
        """
        Get the edge curve geometry

        Returns:
            OCC.Geom.Handle_Geom_Curve: Interface to all curve geometry
        """
        return BRep_Tool_Curve(self._edge)[0]

    def specific_curve(self):
        """
        Get the specific edge curve geometry

        Returns:
            OCC.Geom.Handle_Geom_*: Specific geometry type for the curve geometry
        """
        brep_adaptor_curve = BRepAdaptor_Curve(self._edge)
        curv_type = brep_adaptor_curve.GetType()
        if curv_type == GeomAbs_Line:
            return brep_adaptor_curve.Line()
        if curv_type == GeomAbs_Circle:
            return brep_adaptor_curve.Circle()
        if curv_type == GeomAbs_Ellipse:
            return brep_adaptor_curve.Ellipse()
        if curv_type == GeomAbs_Hyperbola:
            return brep_adaptor_curve.Hyperbola()
        if curv_type == GeomAbs_Parabola:
            return brep_adaptor_curve.Parabola()
        if curv_type == GeomAbs_BezierCurve:
            return brep_adaptor_curve.BezierCurve()
        if curv_type == GeomAbs_BSplineCurve:
            return brep_adaptor_curve.BSplineCurve()
        if curv_type == GeomAbs_OffsetCurve:
            return brep_adaptor_curve.OffsetCurve()
        raise ValueError("Unknown curve type: ", curv_type)

    def has_curve(self):
        """
        Does this edge have a valid curve?
        Some edges don't.  For example the edge at the pole of a sphere.

        Returns:
            bool: Whether this edge has a valid curve
        """
        curve = BRepAdaptor_Curve(self.topods_edge())
        return curve.Is3DCurve() 

    def u_bounds(self):
        """
        Parameter domain of the curve

        Returns:
            occwl.geometry.Interval: a 1D interval [u_min, u_max]
        """
        if not self.has_curve():
            # Return an empty interval
            return Interval()
        _, umin, umax = BRep_Tool_Curve(self.topods_edge())
        return Interval(umin, umax)
    
    def twin_edge(self):
        raise NotImplementedError

    def convex(self):
        """
        Returns the convex flag associated with the edge
        NOTE: this does not check for edge convexity

        Returns:
            bool: the Convex flag set in the edge
        """
        return self.topods_edge().Convex()
    
    def closed(self):
        """
        Whether the curve is closed

        Returns:
            bool: If closed
        """
        return self.topods_edge().Closed()

    def seam(self, face):
        """
        Whether this edge is a seam

        Args:
            face (occwl.face.Face): Face where the edge lives

        Returns:
            bool: If seam
        """
        return ShapeAnalysis_Edge().IsSeam(self.topods_edge(), face.topods_face())

    def periodic(self):
        """
        Whether this edge is periodic

        Returns:
            bool: If periodic
        """
        return BRepAdaptor_Curve(self.topods_edge()).IsPeriodic()

    def rational(self):
        """
        Whether this edge geometry is rational

        Returns:
            bool: If rational
        """
        return BRepAdaptor_Curve(self.topods_edge()).IsRational()

    def continuity(self, face1, face2):
        """
        Get the order of continuity among a pair of faces

        Args:
            face1 (occwl.face.Face): First face
            face2 (occwl.face.Face): Second face

        Returns:
            GeomAbs_Shape: enum describing the continuity order
        """
        return BRep_Tool_Continuity(self.topods_edge(), face1.topods_face(), face2.topods_face())

    def reversed(self):
        """
        Whether this edge is reversed with respect to the curve geometry

        Returns:
            bool: If rational
        """
        return self.topods_edge().Orientation() == TopAbs_REVERSED
    
    def curve_type(self):
        """
        Get the type of the curve geometry

        Returns:
            str: Type of the curve geometry
        """
        curv_type = BRepAdaptor_Curve(self._edge).GetType()
        if curv_type == GeomAbs_Line:
            return "line"
        if curv_type == GeomAbs_Circle:
            return "circle"
        if curv_type == GeomAbs_Ellipse:
            return "ellipse"
        if curv_type == GeomAbs_Hyperbola:
            return "hyperbola"
        if curv_type == GeomAbs_Parabola:
            return "parabola"
        if curv_type == GeomAbs_BezierCurve:
            return "bezier"
        if curv_type == GeomAbs_BSplineCurve:
            return "bspline"
        if curv_type == GeomAbs_OffsetCurve:
            return "offset"
        if curv_type == GeomAbs_OtherCurve:
            return "other"
        return "unknown"
