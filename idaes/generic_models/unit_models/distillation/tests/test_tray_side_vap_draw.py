##############################################################################
# Institute for the Design of Advanced Energy Systems Process Systems
# Engineering Framework (IDAES PSE Framework) Copyright (c) 2018-2020, by the
# software owners: The Regents of the University of California, through
# Lawrence Berkeley National Laboratory,  National Technology & Engineering
# Solutions of Sandia, LLC, Carnegie Mellon University, West Virginia
# University Research Corporation, et al. All rights reserved.
#
# Please see the files COPYRIGHT.txt and LICENSE.txt for full copyright and
# license information, respectively. Both files are also available online
# at the URL "https://github.com/IDAES/idaes-pse".
##############################################################################
"""
Tests for conventional tray unit model (no feed, has vap side draw).

Author: Jaffer Ghouse
"""
import pytest
from pyomo.environ import (ConcreteModel, TerminationCondition,
                           SolverStatus, value)

from idaes.core import (FlowsheetBlock, MaterialBalanceType, EnergyBalanceType,
                        MomentumBalanceType)
from idaes.generic_models.unit_models.distillation import Tray
from idaes.generic_models.properties.activity_coeff_models.\
    BTX_activity_coeff_VLE import BTXParameterBlock
from idaes.core.util.model_statistics import degrees_of_freedom, \
    number_variables, number_total_constraints, number_unused_variables, \
    fixed_variables_set, activated_constraints_set
from idaes.core.util.testing import get_default_solver, \
    PhysicalParameterTestBlock, initialization_tester


# -----------------------------------------------------------------------------
# Get default solver for testing
solver = get_default_solver()


def test_config():

    m = ConcreteModel()
    m.fs = FlowsheetBlock(default={"dynamic": False})
    m.fs.properties = PhysicalParameterTestBlock()

    m.fs.unit = Tray(default={"property_package": m.fs.properties,
                              "has_vapor_side_draw": True,
                              "has_heat_transfer": True,
                              "has_pressure_change": True})

    assert len(m.fs.unit.config) == 9

    assert not m.fs.unit.config.is_feed_tray
    assert not m.fs.unit.config.has_liquid_side_draw
    assert m.fs.unit.config.has_vapor_side_draw


class TestBTXIdeal(object):
    @pytest.fixture(scope="class")
    def btx_ftpz(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = BTXParameterBlock(default={"valid_phase":
                                                     ('Liq', 'Vap'),
                                                     "activity_coeff_model":
                                                     "Ideal"})
        m.fs.unit = Tray(default={"property_package": m.fs.properties,
                                  "has_vapor_side_draw": True,
                                  "has_heat_transfer": True,
                                  "has_pressure_change": True})
        return m

    @pytest.fixture(scope="class")
    def btx_fctp(self):
        m = ConcreteModel()
        m.fs = FlowsheetBlock(default={"dynamic": False})

        m.fs.properties = BTXParameterBlock(default={"valid_phase":
                                                     ('Liq', 'Vap'),
                                                     "activity_coeff_model":
                                                     "Ideal",
                                                     "state_vars": "FcTP"})
        m.fs.unit = Tray(default={"property_package": m.fs.properties,
                                  "has_vapor_side_draw": True,
                                  "has_heat_transfer": True,
                                  "has_pressure_change": True})
        return m

    @pytest.mark.build
    def test_build(self, btx_ftpz, btx_fctp):
        # General build
        assert hasattr(btx_ftpz.fs.unit, "material_mixing_equations")
        assert hasattr(btx_ftpz.fs.unit, "enthalpy_mixing_equations")
        assert hasattr(btx_ftpz.fs.unit, "pressure_drop_equation")

        assert btx_ftpz.fs.unit.config.has_heat_transfer
        assert hasattr(btx_ftpz.fs.unit, "heat_duty")

        assert btx_ftpz.fs.unit.config.has_pressure_change
        assert hasattr(btx_ftpz.fs.unit, "deltaP")

        # State blocks
        assert hasattr(btx_ftpz.fs.unit, "properties_in_liq")
        assert hasattr(btx_ftpz.fs.unit, "properties_in_vap")
        assert hasattr(btx_ftpz.fs.unit, "properties_out")

        # Ports
        assert hasattr(btx_ftpz.fs.unit, "liq_in")
        assert hasattr(btx_ftpz.fs.unit.liq_in, "flow_mol")
        assert hasattr(btx_ftpz.fs.unit.liq_in, "mole_frac_comp")
        assert hasattr(btx_ftpz.fs.unit.liq_in, "temperature")
        assert hasattr(btx_ftpz.fs.unit.liq_in, "pressure")

        assert hasattr(btx_ftpz.fs.unit, "vap_in")
        assert hasattr(btx_ftpz.fs.unit.vap_in, "flow_mol")
        assert hasattr(btx_ftpz.fs.unit.vap_in, "mole_frac_comp")
        assert hasattr(btx_ftpz.fs.unit.vap_in, "temperature")
        assert hasattr(btx_ftpz.fs.unit.vap_in, "pressure")

        assert hasattr(btx_ftpz.fs.unit, "liq_out")
        assert hasattr(btx_ftpz.fs.unit.liq_out, "flow_mol")
        assert hasattr(btx_ftpz.fs.unit.liq_out, "mole_frac_comp")
        assert hasattr(btx_ftpz.fs.unit.liq_out, "temperature")
        assert hasattr(btx_ftpz.fs.unit.liq_out, "pressure")

        assert hasattr(btx_ftpz.fs.unit, "vap_out")
        assert hasattr(btx_ftpz.fs.unit.vap_out, "flow_mol")
        assert hasattr(btx_ftpz.fs.unit.vap_out, "mole_frac_comp")
        assert hasattr(btx_ftpz.fs.unit.vap_out, "temperature")
        assert hasattr(btx_ftpz.fs.unit.vap_out, "pressure")

        assert not hasattr(btx_ftpz.fs.unit, "liq_side_draw")
        assert not hasattr(btx_ftpz.fs.unit, "liq_side_sf")

        assert hasattr(btx_ftpz.fs.unit, "vap_side_draw")
        assert hasattr(btx_ftpz.fs.unit, "vap_side_sf")

        assert number_variables(btx_ftpz.fs.unit) == 72
        assert number_total_constraints(btx_ftpz.fs.unit) == 59
        assert number_unused_variables(btx_ftpz) == 1

        # General build
        assert hasattr(btx_fctp.fs.unit, "material_mixing_equations")
        assert hasattr(btx_fctp.fs.unit, "enthalpy_mixing_equations")
        assert hasattr(btx_fctp.fs.unit, "pressure_drop_equation")

        assert btx_fctp.fs.unit.config.has_heat_transfer
        assert hasattr(btx_fctp.fs.unit, "heat_duty")

        assert btx_fctp.fs.unit.config.has_pressure_change
        assert hasattr(btx_fctp.fs.unit, "deltaP")

        # State blocks
        assert hasattr(btx_fctp.fs.unit, "properties_in_liq")
        assert hasattr(btx_fctp.fs.unit, "properties_in_vap")
        assert hasattr(btx_fctp.fs.unit, "properties_out")

        # Ports
        assert hasattr(btx_fctp.fs.unit, "liq_in")
        assert hasattr(btx_fctp.fs.unit.liq_in, "flow_mol_comp")
        assert hasattr(btx_fctp.fs.unit.liq_in, "temperature")
        assert hasattr(btx_fctp.fs.unit.liq_in, "pressure")

        assert hasattr(btx_fctp.fs.unit, "vap_in")
        assert hasattr(btx_fctp.fs.unit.vap_in, "flow_mol_comp")
        assert hasattr(btx_fctp.fs.unit.vap_in, "temperature")
        assert hasattr(btx_fctp.fs.unit.vap_in, "pressure")

        assert hasattr(btx_fctp.fs.unit, "liq_out")
        assert hasattr(btx_fctp.fs.unit.liq_out, "flow_mol_comp")
        assert hasattr(btx_fctp.fs.unit.liq_out, "temperature")
        assert hasattr(btx_fctp.fs.unit.liq_out, "pressure")

        assert hasattr(btx_fctp.fs.unit, "vap_out")
        assert hasattr(btx_fctp.fs.unit.vap_out, "flow_mol_comp")
        assert hasattr(btx_fctp.fs.unit.vap_out, "temperature")
        assert hasattr(btx_fctp.fs.unit.vap_out, "pressure")

        assert not hasattr(btx_fctp.fs.unit, "liq_side_draw")
        assert not hasattr(btx_fctp.fs.unit, "liq_side_sf")

        assert hasattr(btx_fctp.fs.unit, "vap_side_draw")
        assert hasattr(btx_fctp.fs.unit, "vap_side_sf")

        assert number_variables(btx_fctp.fs.unit) == 75
        assert number_total_constraints(btx_fctp.fs.unit) == 64
        assert number_unused_variables(btx_fctp) == 1

    def test_dof(self, btx_ftpz, btx_fctp):

        # Set inputs
        btx_ftpz.fs.unit.liq_in.flow_mol.fix(1)
        btx_ftpz.fs.unit.liq_in.temperature.fix(369)
        btx_ftpz.fs.unit.liq_in.pressure.fix(101325)
        btx_ftpz.fs.unit.liq_in.mole_frac_comp[0, "benzene"].fix(0.5)
        btx_ftpz.fs.unit.liq_in.mole_frac_comp[0, "toluene"].fix(0.5)

        btx_ftpz.fs.unit.vap_in.flow_mol.fix(1)
        btx_ftpz.fs.unit.vap_in.temperature.fix(372)
        btx_ftpz.fs.unit.vap_in.pressure.fix(101325)
        btx_ftpz.fs.unit.vap_in.mole_frac_comp[0, "benzene"].fix(0.5)
        btx_ftpz.fs.unit.vap_in.mole_frac_comp[0, "toluene"].fix(0.5)

        btx_ftpz.fs.unit.deltaP.fix(0)
        btx_ftpz.fs.unit.heat_duty.fix(0)

        btx_ftpz.fs.unit.vap_side_sf.fix(0.5)

        assert degrees_of_freedom(btx_ftpz.fs.unit) == 0

        # Set inputs
        btx_fctp.fs.unit.liq_in.flow_mol_comp[0, "benzene"].fix(0.5)
        btx_fctp.fs.unit.liq_in.flow_mol_comp[0, "toluene"].fix(0.5)
        btx_fctp.fs.unit.liq_in.temperature.fix(369)
        btx_fctp.fs.unit.liq_in.pressure.fix(101325)

        btx_fctp.fs.unit.vap_in.flow_mol_comp[0, "benzene"].fix(0.5)
        btx_fctp.fs.unit.vap_in.flow_mol_comp[0, "toluene"].fix(0.5)
        btx_fctp.fs.unit.vap_in.temperature.fix(372)
        btx_fctp.fs.unit.vap_in.pressure.fix(101325)

        btx_fctp.fs.unit.deltaP.fix(0)
        btx_fctp.fs.unit.heat_duty.fix(0)
        btx_fctp.fs.unit.vap_side_sf.fix(0.5)

        assert degrees_of_freedom(btx_fctp.fs.unit) == 0

    @pytest.mark.initialization
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_initialize(self, btx_ftpz, btx_fctp):
        initialization_tester(btx_ftpz)
        initialization_tester(btx_fctp)

    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solve(self, btx_ftpz, btx_fctp):

        results = solver.solve(btx_ftpz)

        # Check for optimal solution
        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

        results = solver.solve(btx_fctp)

        # Check for optimal solution
        assert results.solver.termination_condition == \
            TerminationCondition.optimal
        assert results.solver.status == SolverStatus.ok

    @pytest.mark.initialize
    @pytest.mark.solver
    @pytest.mark.skipif(solver is None, reason="Solver not available")
    def test_solution(self, btx_ftpz, btx_fctp):

        # liq_out port
        assert (pytest.approx(0.46337, abs=1e-3) ==
                value(btx_ftpz.fs.unit.liq_out.flow_mol[0]))
        assert (pytest.approx(0.33313, abs=1e-3) ==
                value(btx_ftpz.fs.unit.liq_out.mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.66686, abs=1e-3) ==
                value(btx_ftpz.fs.unit.liq_out.mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(370.567, abs=1e-3) ==
                value(btx_ftpz.fs.unit.liq_out.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz.fs.unit.liq_out.pressure[0]))

        # vap_out port
        assert (pytest.approx(0.76831, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_out.flow_mol[0]))
        assert (pytest.approx(0.55031, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_out.mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.44968, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_out.mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(370.567, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_out.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_out.pressure[0]))

        # side vap_out port
        assert (pytest.approx(0.76831, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_side_draw.flow_mol[0]))
        assert (pytest.approx(0.55031, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_side_draw.
                mole_frac_comp[0, "benzene"]))
        assert (pytest.approx(0.44968, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_side_draw.
                mole_frac_comp[0, "toluene"]))
        assert (pytest.approx(370.567, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_side_draw.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_ftpz.fs.unit.vap_side_draw.pressure[0]))

        # liq_out port
        assert (pytest.approx(0.15436, abs=1e-3) ==
                value(btx_fctp.fs.unit.liq_out.flow_mol_comp[0, "benzene"]))
        assert (pytest.approx(0.30900, abs=1e-3) ==
                value(btx_fctp.fs.unit.liq_out.flow_mol_comp[0, "toluene"]))
        assert (pytest.approx(370.567, abs=1e-3) ==
                value(btx_fctp.fs.unit.liq_out.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_fctp.fs.unit.liq_out.pressure[0]))

        # vap_out port
        assert (pytest.approx(0.42280, abs=1e-3) ==
                value(btx_fctp.fs.unit.vap_out.flow_mol_comp[0, "benzene"]))
        assert (pytest.approx(0.34549, abs=1e-3) ==
                value(btx_fctp.fs.unit.vap_out.flow_mol_comp[0, "toluene"]))
        assert (pytest.approx(370.567, abs=1e-3) ==
                value(btx_fctp.fs.unit.vap_out.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_fctp.fs.unit.vap_out.pressure[0]))

        # side vap_out port
        assert (pytest.approx(0.4228, abs=1e-3) ==
                value(btx_fctp.fs.unit.vap_side_draw.
                flow_mol_comp[0, "benzene"]))
        assert (pytest.approx(0.34549, abs=1e-3) ==
                value(btx_fctp.fs.unit.vap_side_draw.
                flow_mol_comp[0, "toluene"]))
        assert (pytest.approx(370.567, abs=1e-3) ==
                value(btx_fctp.fs.unit.vap_side_draw.temperature[0]))
        assert (pytest.approx(101325, abs=1e-3) ==
                value(btx_fctp.fs.unit.vap_side_draw.pressure[0]))