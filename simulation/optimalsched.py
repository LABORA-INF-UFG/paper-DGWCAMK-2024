from typing import Dict

from pyomo import environ as pyo
from simulation.simulation import Simulation
from simulation.discretebuffer import DiscreteBuffer

def optimize(sim: Simulation, method: str, allocate_all_resources = False, verbose=False):
    '''
    Function for building and solving the linear model.

    Parameters
    ----------
    sim: Simulation
        Input data for building the model.
    
    method: str
        Lower case string with the solver's name (e.g. cplex or gurobi)  
    
    allocate_all_resources: bool, optional
        Flag that indicates how to constraint the slice RBGs. If true. then sum(R_s) == R.
        Else, sum(R_s) <= R and the allocation is minimized.

    verbose: bool, optional
        Flag for verbose solving.
    
    Returns
    -------
    ConcreteModel
        The built and solved model with values accessible by using m.var_name.value attribute.
    Unknow Type
        Results from the solving process.
    '''
    if verbose:
        print ("Building model...")

    # PREPROCESSING
    u_buff:Dict[int, DiscreteBuffer] = dict()
    for u in sim.users.values():
        u_buff[u.id] = u.get_discrete_buffer()
    l_max = len(u_buff.values()[0].buff)

    m = pyo.ConcreteModel()

    # ----
    # SETS
    # ----

    # SET: S
    m.S = pyo.Set(initialize = sim.slices.keys())

    # SET: S_rlp_
    m.S_rlp = pyo.Set(initialize = [s.id for s in sim.slices.values() if s.type == "embb" or s.type == "urllc"])
    
    # SET: S_fg
    m.S_fg = pyo.Set(initialize = [s.id for s in sim.slices.values() if s.type == "be"])

    # SET: U
    m.U = pyo.Set(initialize = sim.users.keys())

    # SET: U_rlp
    m.U_rlp = pyo.Set(initialize = [u.id for s in m.S_rlp for u in sim.slices[s].users.keys()])

    # SET: U_fg
    m.U_fg = pyo.Set(initialize = [u.id for s in m.S_fg for u in sim.slices[s].users.keys()])

    # SET: i = 0, ..., l_{max}
    for u in sim.users.values():
        u.max
    m.I = pyo.Set(initialize = range(len(u_buff.values()[0].buff)))

    # Set: i = 0, ..., l_{max} - 1
    m.I_0_l_max_1 = pyo.Set(initialize = range(data.l_max))

    # Set: i = 1, ..., l_{max}
    m.I_1_l_max = pyo.Set(initialize = range(1, data.l_max+1))

    # ----
    # VARS
    # ----

    # VAR: R_s for all slices
    m.R_s = pyo.Var(m.S, domain=pyo.NonNegativeIntegers)

    # VAR: a_s for all slices
    #m.a_s = pyo.Var(m.S, domain=pyo.NonNegativeIntegers)

    # VAR: R_u for all users
    m.R_u = pyo.Var(m.U, domain=pyo.NonNegativeIntegers)

    # VAR: k_u for all users
    m.k_u = pyo.Var(m.U, domain=pyo.NonNegativeIntegers)
    
    # VAR: sent_u^i for rlp users
    m.sent_u_i = pyo.Var(m.U_rlp, m.I, domain=pyo.NonNegativeIntegers)
    
    # VAR: T_u for rlp users
    m.T_u = pyo.Var(m.U_rlp, domain=pyo.NonNegativeIntegers)

    # VAR: MAXover_u for rlp users
    m.MAXover_u = pyo.Var(m.U_rlp, domain=pyo.NonNegativeIntegers)

    # VAR: alpha_u for rlp users
    m.alpha_u = pyo.Var(m.U_rlp, domain=pyo.Binary)

    # VAR: delta_u_i for rlp users
    m.delta_u_i = pyo.Var(m.U_rlp, m.I_1_l_max, domain=pyo.Binary)

    # VAR: beta_u for rlp users
    m.beta_u = pyo.Var(m.U_rlp, domain=pyo.Binary)

    if data.n > 0:
        # VAR: psi_u for fg users if n >= 1
        m.psi_u = pyo.Var(m.U_fg, domain=pyo.Binary)

    if data.n > 1:
        # VAR: rho_u for fg users if n >= 2
        m.rho_u = pyo.Var(m.U_fg, domain=pyo.Binary)

        # VAR: lambda_u for fg users if n >= 2
        m.lambda_u = pyo.Var(m.U_fg, domain=pyo.Binary)

        # VAR: sigma_u for fg users if n >= 2
        m.sigma_u = pyo.Var(m.U_fg, domain=pyo.Binary)

        # VAR: omega_u for fg users if n >= 2
        m.omega_u = pyo.Var(m.U_fg, domain=pyo.Binary)

    # -----------
    # EXPRESSIONS
    # -----------

    # --------------- Global expressions
    
    # EXP: V_r the upper bound for any r_s
    V_r = data.B * max(data.users[u].SE[data.n] for u in m.U)

    # EXP: V_T the upper bound for any T_u
    V_T = V_r/data.PS + data.b_max

    # EXP v_sent the lower bound for any sent_u_i - buff_u_i
    v_sent = -data.b_max

    # EXP V_sent the upper bound for any sent_u_i - buff_u_i
    V_sent = int(V_r/data.PS)

    # EXP: V_over the upper bound of any b_u_sup
    V_over = data.b_max + max(data.users[u].hist_rcv[data.n] for u in m.U)


    # --------------- Expressions for all slices

    # R_s = dict()
    # for s in m.S:
    #     # EXP: R_s calculation for all slices
    #     R_s[s] = m.a_s[s] * len(U_s[s])
    
    # --------------- Expressions for all users

    #R_u = dict()
    r_u = dict()
    for u in m.U:
        s = data.users[u].s
        # EXP: R_u calculation for all users
        #R_u[u] = R_s[s] / len(U_s[s])

        # EXP: r_u calculation for all users
        #r_u[u] = data.B * (R_u[u]/data.R) * data.users[u].SE[data.n] / 1e3
        r_u[u] = data.B * (m.R_u[u]/data.R) * data.users[u].SE[data.n] / 1e3

    # --------------- Expressions for rlp users
    
    remain_u_i = dict()
    b_u_sup = dict()
    over_u = dict()
    d_u_sup = dict()
    p_u = dict()
    for u in m.U_rlp:
        for i in m.I:
            # EXP: remain_u_i = buff_u_i - sent_u_i for rlp users
            remain_u_i[u,i] = data.users[u].hist_buff[data.n][i] - m.sent_u_i[u,i]
    
        # EXP: b_u_sup for rlp users
        b_u_sup[u] = data.users[u].hist_rcv[data.n] + sum(remain_u_i[u,i] for i in m.I)
    
        # EXP: over_u for rlp users
        over_u[u] = m.MAXover_u[u] - data.b_max

        # EXP: d_u_sup for rlp users
        d_u_sup[u] = remain_u_i[u, data.l_max] + over_u[u]

        # EXP: p_u for rlp users
        denominator = data.users[u].hist_b[data.n-data.users[u].w+1] + data.users[u].hist_rcv[data.n] + sum(data.users[u].hist_rcv[data.n-data.users[u].w+2 : data.n+1])
        if denominator > 0:
            p_u[u] = d_u_sup[u] + sum(data.users[u].hist_d[data.n-data.users[u].w+1 : data.n+1]) / denominator
        else:
            p_u[u] = 0*d_u_sup[u]
    
    # --------------- Expressions for fg users
    
    g_u = dict()
    for u in m.U_fg:
        # EXP: g_u calculation
        g_u[u] = (sum(data.users[u].hist_r[data.n-data.users[u].w+1 : data.n]) + r_u[u])/data.users[u].w

    # ------------------
    # OBJECTIVE FUNCTION
    # ------------------

    # OBJ: min sum R_s
    #m.OBJECTIVE = pyo.Objective(expr=sum(R_s[s] for s in m.S), sense=pyo.minimize)
    m.OBJECTIVE = pyo.Objective(expr=sum(m.R_s[s] for s in m.S), sense=pyo.minimize)


    # -----------
    # CONSTRAINTS
    # -----------

    # --------------- Global constraints

    # CONSTR: sum R_s = R
    if allocate_all_resources:
        #m.constr_R_s_sum = pyo.Constraint(expr=sum(R_s[s] for s in m.S) == data.R)
        m.constr_R_s_sum = pyo.Constraint(expr=sum(m.R_s[s] for s in m.S) == data.R)
    else:
        #m.constr_R_s_sum = pyo.Constraint(expr=sum(R_s[s] for s in m.S) <= data.R)
        m.constr_R_s_sum = pyo.Constraint(expr=sum(m.R_s[s] for s in m.S) <= data.R)

    # --------------- Constraints for all slices
    
    m.constr_R_u_sum = pyo.ConstraintList()
    m.constr_R_u_prioritization = pyo.ConstraintList()
    for s in m.S:
        # CONSTR: sum R_u = R_s
        m.constr_R_u_sum.add(
            sum(m.R_u[u] for u in U_s[s]) == m.R_s[s]
        )

        ue_indexes = data.slices[s].users.keys()
        prior = data.slices[s].rr_prioritization
        
        for i in range (len(prior)-1):
            # CONSTR: R_u prioritization
            m.constr_R_u_prioritization.add(
                m.R_u[prior[i]] - m.R_u[prior[i+1]] >= 0
            )
    
    # --------------- Constraints for all users
    
    m.constr_R_u_1 = pyo.ConstraintList()
    m.constr_R_u_2 = pyo.ConstraintList()
    for u in m.U:
        s = data.users[u].s

        # CONSTR: R_u intra slice modeling upper bound
        m.constr_R_u_1.add(
            m.R_u[u] - m.R_s[s]/len(U_s[s]) <= 1 - data.e
        )
        
        # CONSTR: R_u intra slice modeling lower bound
        m.constr_R_u_2.add(
            m.R_s[data.users[u].s]/len(U_s[s]) - m.R_u[u] <= 1 - data.e
        )

    # --------------- Constraints for fg users
    
    m.constr_g_u_intent = pyo.ConstraintList()
    m.constr_f_u_intent = pyo.ConstraintList()
    m.constr_psi_u_le = pyo.ConstraintList()
    m.constr_psi_u_ge = pyo.ConstraintList()
    m.constr_rho_u_le = pyo.ConstraintList()
    m.constr_rho_u_ge = pyo.ConstraintList()
    m.constr_lambda_u_le = pyo.ConstraintList()
    m.constr_lambda_u_ge = pyo.ConstraintList()
    m.constr_sigma_u_le = pyo.ConstraintList()
    m.constr_sigma_u_ge = pyo.ConstraintList()
    m.constr_omega_u_le = pyo.ConstraintList()
    m.constr_omega_u_ge = pyo.ConstraintList()
    for u in m.U_fg:
        s = data.users[u].s
        
        # CONSTR: Long-term Throughput intent
        if data.users[u].w == 1:
            m.constr_g_u_intent.add(
                r_u[u] >= data.users[u].g_req
            )
        else:
            m.constr_g_u_intent.add(
                g_u[u] >= data.users[u].g_req
            )
        
        # Fifth-percentile constraints
        if data.users[u].w == 1:
            # CONSTR: Fifth-percentile intent for w = 1
            m.constr_f_u_intent.add(
                r_u[u] >= data.users[u].f_req
            )    
        elif data.users[u].w < 20:
            sort_h = data.users[u].getSortedThroughputWindow(data.users[u].w, data.n)[0]
            
            # CONSTR: Psi upper bound
            m.constr_psi_u_le.add(
                r_u[u] + V_r * m.psi_u[u] <= V_r + sort_h
            )
            
            # CONSTR: Psi lower bound
            m.constr_psi_u_ge.add(
                r_u[u] + (sort_h + data.e) * m.psi_u[u] >= sort_h + data.e
            )
            
            # CONSTR: Fifth-percentile intent for n = 1
            m.constr_f_u_intent.add(
                r_u[u] >= m.psi_u[u] * data.users[u].f_req
            )
            
        else:
            sort = data.users[u].getSortedThroughputWindow(data.users[u].w, data.n)
            h = int((data.users[u].w)/20)
            sort_h_1 = sort[h-1]
            sort_h = sort[h]

            # CONSTR: Psi upper bound
            m.constr_psi_u_le.add(
                r_u[u] + V_r * m.psi_u[u] <= V_r + sort_h_1
            )
            
            # CONSTR: Psi lower bound
            m.constr_psi_u_ge.add(
                r_u[u] + (sort_h_1 + data.e) * m.psi_u[u] >= sort_h_1 + data.e
            )

            # CONSTR: Rho upper bound
            m.constr_rho_u_le.add(
                r_u[u] + V_r * m.rho_u[u] <= V_r + sort_h
            )
            
            # CONSTR: Rho lower bound
            m.constr_rho_u_ge.add(
                r_u[u] + (sort_h + data.e) * m.rho_u[u] >= sort_h + data.e
            )

            # CONSTR: Lambda upper bound
            m.constr_lambda_u_le.add(
                m.psi_u[u] + m.rho_u[u] - 2*m.lambda_u[u] >= 0
            )
            
            # CONSTR: Lambda lower bound
            m.constr_lambda_u_ge.add(
                m.psi_u[u] + m.rho_u[u] - data.e * m.lambda_u[u] <= 2 - data.e
            )

            # CONSTR: Sigma upper bound
            m.constr_sigma_u_le.add(
                m.psi_u[u] + m.rho_u[u] + 2*m.sigma_u[u] <= 2
            )
            
            # CONSTR: Sigma lower bound
            m.constr_sigma_u_ge.add(
                m.psi_u[u] + m.rho_u[u] + data.e * m.sigma_u[u] >= data.e
            )

            # CONSTR: Omega upper bound
            m.constr_omega_u_le.add(
                m.lambda_u[u] + m.sigma_u[u] + 2*m.omega_u[u] <= 2
            )
            
            # CONSTR: Omega lower bound
            m.constr_omega_u_ge.add(
                m.lambda_u[u] + m.sigma_u[u] + data.e * m.omega_u[u] >= data.e
            )
            
            # CONSTR: Fifth-percentile intent for w > 20
            m.constr_f_u_intent.add(
                r_u[u] >= m.omega_u[u] * data.users[u].f_req
            )
            
    
    # --------------- Constraints for rlp users
    m.constr_k_u_floor_upper = pyo.ConstraintList()
    m.constr_k_u_floor_lower = pyo.ConstraintList()
    m.constr_r_u_intent = pyo.ConstraintList()
    m.constr_sent_l_max = pyo.ConstraintList()
    m.constr_sent_T_u = pyo.ConstraintList()
    m.constr_T_u_le_k_u = pyo.ConstraintList()
    m.constr_T_u_le_sum_buff_u = pyo.ConstraintList()
    m.constr_T_u_ge_k_u = pyo.ConstraintList()
    m.constr_T_u_ge_sum_buff_u = pyo.ConstraintList()
    m.constr_sent_le_delta_buff = pyo.ConstraintList()
    m.constr_delta_u_i_ge = pyo.ConstraintList()
    m.constr_delta_u_i_le = pyo.ConstraintList()
    m.constr_l_u_intent = pyo.ConstraintList()
    m.constr_maxover_u_ge_b_u_sup = pyo.ConstraintList()
    m.constr_maxover_u_ge_b_max = pyo.ConstraintList()
    m.constr_maxover_u_le_b_u_sup = pyo.ConstraintList()
    m.constr_maxover_u_le_b_max = pyo.ConstraintList()
    m.constr_p_u_intent = pyo.ConstraintList()
    for u in m.U_rlp:
        
        # CONSTR: Throughput intent
        m.constr_r_u_intent.add(
            r_u[u] >= data.users[u].r_req
        )
        
        # CONSTR: k_u flooring upper bound
        m.constr_k_u_floor_upper.add(
            m.k_u[u] <= r_u[u]/data.PS + data.users[u].hist_part[data.n]
        )

        # CONSTR: k_u flooring lower bound
        m.constr_k_u_floor_lower.add(
            m.k_u[u] + 1 >= r_u[u]/data.PS + data.users[u].hist_part[data.n] + data.e
        )

        # CONSTR: sent_l_max <= buffer_l_max
        m.constr_sent_l_max.add(
            m.sent_u_i[u,data.l_max] <= data.users[u].hist_buff[data.n][data.l_max]
        )

        # CONSTR: sum sent_u_i  = T_u
        m.constr_sent_T_u.add(
            sum(m.sent_u_i[u,i] for i in m.I) == m.T_u[u]
        )

        # CONSTR: T_u <= k_u
        m.constr_T_u_le_k_u.add(
            m.T_u[u] <= m.k_u[u]
        )

        # CONSTR: T_u <= sum buff_u
        m.constr_T_u_le_sum_buff_u.add(
            m.T_u[u] <= sum(data.users[u].hist_buff[data.n][i] for i in m.I)
        )

        # CONSTR: T_u >= k_u
        m.constr_T_u_ge_k_u.add(
            m.T_u[u] >= m.k_u[u] - V_T * (1 - m.alpha_u[u])
        )

        # CONSTR: T_u >= sum buff_u
        m.constr_T_u_ge_sum_buff_u.add(
            m.T_u[u] >= sum(data.users[u].hist_buff[data.n][i] for i in m.I) - V_T * m.alpha_u[u]
        )
        
        for i in m.I_0_l_max_1:
            # CONSTR: sent_u_i <= delta_u_i * buff_u
            m.constr_sent_le_delta_buff.add(
                m.sent_u_i[u,i] <= m.delta_u_i[u,i+1] * data.users[u].hist_buff[data.n][i]
            )
        
        for i in m.I_1_l_max:
            
            # CONSTR: delta_u_i lower bound
            m.constr_delta_u_i_ge.add(
                m.sent_u_i[u,i] + v_sent * m.delta_u_i[u,i] >= v_sent + data.users[u].hist_buff[data.n][i]
            )

            # CONSTR: delta_u_i upper bound
            m.constr_delta_u_i_le.add(
                m.sent_u_i[u,i] - (V_sent + data.e) * m.delta_u_i[u,i] <= data.users[u].hist_buff[data.n][i] - data.e
            )
        
        # CONSTR: Average Buffer Latency intent
        m.constr_l_u_intent.add(
            sum((data.users[u].hist_acc[data.n][i] + m.sent_u_i[u,i])*i for i in m.I)
            <= data.users[u].l_req * sum((data.users[u].hist_acc[data.n][i] + m.sent_u_i[u,i]) for i in m.I)
        )
        
        # CONSTR: maxover_u >= b_u_sup
        m.constr_maxover_u_ge_b_u_sup.add(
            m.MAXover_u[u] >= b_u_sup[u]
        )

        # CONSTR: maxover_u >= b_max
        m.constr_maxover_u_ge_b_max.add(
            m.MAXover_u[u] >= data.b_max
        )
        
        # CONSTR: maxover_u <= b_u_sup
        m.constr_maxover_u_le_b_u_sup.add(
            m.MAXover_u[u] <= b_u_sup[u] + V_over * (1 - m.beta_u[u])
        )
        
        # CONSTR: maxover_u <= b_max
        m.constr_maxover_u_le_b_max.add(
            m.MAXover_u[u] <= data.b_max + V_over * m.beta_u[u]
        )
        
        # CONSTR: Packet Loss Rate intent
        m.constr_p_u_intent.add(
            p_u[u] <= data.users[u].p_req
        )
        
        
    # ----------
    # DUAL MODEL
    # ----------

    #m.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT_EXPORT) # I don't actually know if this works

    # -------
    # SOLVING
    # -------
    if verbose:
        print("Model built!")
        print("Number of constraints =",m.nconstraints())
        print("Number of variables =",m.nvariables())
        print("Starting solving via {}...".format(method))

    opt = pyo.SolverFactory(method)
    results = opt.solve(m, tee=verbose)
    
    if verbose:
        print("Solved!")

    return m, results