# NOT USED IN THE FINAL VERSION OF THE PAPER

from typing import Dict, List

from pyomo import environ as pyo
from simulation.slice import Slice
from simulation.user import User
from simulation.rbg import RBG

def optimize(
    slices: Dict[int, Slice],
    users: Dict[int, User],
    rbgs: List[RBG],
    rb_bandwidth: float,
    rbs_per_rbg: int,
    window_size: int,
    e: float,
    method: str,
    allocate_all_resources = False,
    verbose=False
):
    if verbose:
        print ("Building model...")

    if len(users.values()) == 0:
        raise Exception("No users to schedule")

    l_max = users[0].get_max_lat()

    if l_max < 2:
        raise Exception("Maximum latency must be >= 2 TTIs")

    m = pyo.ConcreteModel()

    # ----
    # SETS
    # ----

    # SET: S
    m.S = pyo.Set(initialize = slices.keys())

    # SET: S_rlp_
    m.S_rlp = pyo.Set(initialize = [s.id for s in slices.values() if s.type == "eMBB" or s.type == "URLLC"])
    
    # SET: S_fg
    m.S_fg = pyo.Set(initialize = [s.id for s in slices.values() if s.type == "BE"])

    # SET: U
    m.U = pyo.Set(initialize = users.keys())

    # SET: U_rlp
    m.U_rlp = pyo.Set(initialize = [u for s in m.S_rlp for u in slices[s].users.keys()])

    # SET: U_fg
    m.U_fg = pyo.Set(initialize = [u for s in m.S_fg for u in slices[s].users.keys()])

    # SET: i = 0, ..., l_{max} -1 
    m.I = pyo.Set(initialize = range(l_max))

    # Set: i = 0, ..., l_{max} - 2
    m.I_without_last = pyo.Set(initialize = range(l_max-1))

    # Set: i = 1, ..., l_{max} -1
    m.I_without_first = pyo.Set(initialize = range(1, l_max))

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
    m.delta_u_i = pyo.Var(m.U_rlp, m.I_without_first, domain=pyo.Binary)

    # VAR: beta_u for rlp users
    m.beta_u = pyo.Var(m.U_rlp, domain=pyo.Binary)

    # VAR: psi_u for fg users
    m.psi_u = pyo.Var(m.U_fg, domain=pyo.Binary)

    # -----------
    # EXPRESSIONS
    # -----------

    # --------------- Global expressions
    
    # EXP: V_r the upper bound for any r_s (bits/s)
    V_r = sum(r.bandwidth for r in rbgs) * max(u.SE for u in users.values())

    # EXP: V_T the upper bound for any T_u (packets)
    V_T = max(V_r/u.get_pkt_size() + u.get_buffer_pkt_capacity() for u in users.values())

    # EXP v_sent the lower bound for any sent_u_i - buff_u_i (packets)
    v_sent = -max(int(u.buff.buffer_size/u.buff.pkt_size) for u in users.values())

    # EXP V_sent the upper bound for any sent_u_i - buff_u_i (packets)
    V_sent = max(int(V_r/u.buff.pkt_size) for u in users.values())

    # EXP: V_over the upper bound of any b_u_sup (packets)
    V_over = max(u.get_buffer_pkt_capacity() + u.get_last_arriv_pkts() for u in users.values())
    
    # --------------- Expressions for all users
    
    r_u = dict()
    for u in m.U:
        # EXP: r_u calculation for all users (bits/s)
        r_u[u] = m.R_u[u] * rbs_per_rbg * rb_bandwidth * users[u].SE

    # --------------- Expressions for rlp users
    
    remain_u_i = dict()
    b_u_sup = dict()
    over_u = dict()
    d_u_sup = dict()
    p_u = dict()
    for u in m.U_rlp:
        for i in m.I:
            # EXP: remain_u_i = buff_u_i - sent_u_i for rlp users (packets)
            remain_u_i[u,i] = users[u].get_n_buff_pkts_waited_i_TTIs(i)- m.sent_u_i[u,i]
    
        # EXP: b_u_sup for rlp users (packets)
        b_u_sup[u] = users[u].get_last_arriv_pkts() + sum(remain_u_i[u,i] for i in m.I)
    
        # EXP: over_u for rlp users (packets)
        over_u[u] = m.MAXover_u[u] - users[u].get_buffer_pkt_capacity()

        # EXP: d_u_sup for rlp users (packets)
        d_u_sup[u] = remain_u_i[u, users[u].get_max_lat()-1] + over_u[u]

        # EXP: p_u for rlp users (ratio)
        denominator = users[u].get_buff_pkts(users[u].step-window_size+1) + users[u].get_last_arriv_pkts() + users[u].get_arriv_pkts(window_size)
        if denominator > 0:
            p_u[u] = d_u_sup[u] + users[u].get_dropp_pkts(window_size) / denominator
        else:
            p_u[u] = 0*d_u_sup[u]
    
    # --------------- Expressions for fg users
    
    g_u = dict()
    for u in m.U_fg:
        # EXP: g_u calculation
        if window_size == 1:
            g_u[u] = r_u[u]
        else:
            g_u[u] = (users[u].get_agg_thr(window_size-1) + r_u[u])/window_size

    # ------------------
    # OBJECTIVE FUNCTION
    # ------------------

    # OBJ: min sum R_s
    m.OBJECTIVE = pyo.Objective(expr=sum(m.R_s[s] for s in m.S), sense=pyo.minimize)

    # -----------
    # CONSTRAINTS
    # -----------

    # --------------- Global constraints

    # CONSTR: sum R_s = R
    if allocate_all_resources:
        m.constr_R_s_sum = pyo.Constraint(expr=sum(m.R_s[s] for s in m.S) == len(rbgs))
    else:
        m.constr_R_s_sum = pyo.Constraint(expr=sum(m.R_s[s] for s in m.S) <= len(rbgs))

    # --------------- Constraints for all slices
    
    m.constr_R_u_sum = pyo.ConstraintList()
    m.constr_R_u_prioritization = pyo.ConstraintList()
    for s in m.S:
        # CONSTR: sum R_u = R_s
        m.constr_R_u_sum.add(
            sum(m.R_u[u] for u in slices[s].users.keys()) == m.R_s[s]
        )

        ue_indexes = slices[s].users.keys()
        user_indexes = slices[s].get_round_robin_prior()
        
        for i in range (len(user_indexes)-1):
            # CONSTR: R_u prioritization
            m.constr_R_u_prioritization.add(
                m.R_u[user_indexes[i]] >= m.R_u[user_indexes[i+1]]
            )
    
    # --------------- Constraints for all users
    
    m.constr_R_u_1 = pyo.ConstraintList()
    m.constr_R_u_2 = pyo.ConstraintList()
    for s in slices.keys():
        for u in slices[s].users.keys():
            # CONSTR: R_u intra slice modeling upper bound
            m.constr_R_u_1.add(
                m.R_u[u] - m.R_s[s]/len(slices[s].users) <= 1 - e
            )
            
            # CONSTR: R_u intra slice modeling lower bound
            m.constr_R_u_2.add(
                m.R_s[s]/len(slices[s].users) - m.R_u[u] <= 1 - e
            )

    # --------------- Constraints for fg users
    
    m.constr_g_u_intent = pyo.ConstraintList()
    m.constr_f_u_intent = pyo.ConstraintList()
    m.constr_psi_u_le = pyo.ConstraintList()
    m.constr_psi_u_ge = pyo.ConstraintList()
    for s in m.S_fg:
        for u in slices[s].users.keys():
            # CONSTR: Long-term Throughput intent
            m.constr_g_u_intent.add(
                g_u[u] >= users[u].requirements["long_term_thr"]
            )
            # Fifth-percentile constraints
            if window_size == 1:
                # CONSTR: Fifth-percentile intent for w = 1
                m.constr_f_u_intent.add(
                    r_u[u] >= users[u].requirements["fifth_perc_thr"]
                )
                
            elif window_size < 20:
                sort_0 = users[u].get_min_thr(window_size-1)
                
                # CONSTR: Psi upper bound
                m.constr_psi_u_le.add(
                    r_u[u] + V_r * m.psi_u[u] <= V_r + sort_0
                )
                
                # CONSTR: Psi lower bound
                m.constr_psi_u_ge.add(
                    r_u[u] + (sort_0 + e) * m.psi_u[u] >= sort_0 + e
                )
                
                # CONSTR: Fifth-percentile intent for n = 1
                m.constr_f_u_intent.add(
                    r_u[u] >= m.psi_u[u] * users[u].requirements["fifth_perc_thr"]
                )
                
            else:
                raise Exception("Window size must be between 1 and 19")
    
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
            r_u[u] >= users[u].requirements["throughput"]
        )

        # CONSTR: k_u flooring upper bound
        m.constr_k_u_floor_upper.add(
            m.k_u[u] <= (r_u[u]*users[u].TTI + users[u].get_part_sent_bits())/users[u].get_pkt_size()
        )

        # CONSTR: k_u flooring lower bound
        m.constr_k_u_floor_lower.add(
            m.k_u[u] + 1 >= (r_u[u]*users[u].TTI + users[u].get_part_sent_bits())/users[u].get_pkt_size() + e
        )

        max_lat = users[u].get_max_lat()

        # CONSTR: sent_l_max_1 <= buffer_l_max_1
        m.constr_sent_l_max.add(
            m.sent_u_i[u, max_lat-1] <= users[u].get_n_buff_pkts_waited_i_TTIs(max_lat-1) 
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
            m.T_u[u] <= users[u].get_buff_pkts_now()
        )

        # CONSTR: T_u >= k_u
        m.constr_T_u_ge_k_u.add(
            m.T_u[u] >= m.k_u[u] - V_T * (1 - m.alpha_u[u])
        )

        # CONSTR: T_u >= sum buff_u
        m.constr_T_u_ge_sum_buff_u.add(
            m.T_u[u] >= users[u].get_buff_pkts_now() - V_T * m.alpha_u[u]
        )
        
        for i in m.I_without_last:
            # CONSTR: sent_u_i <= delta_u_i * buff_u_i
            m.constr_sent_le_delta_buff.add(
                m.sent_u_i[u,i] <= m.delta_u_i[u,i+1] * users[u].get_n_buff_pkts_waited_i_TTIs(i) 
            )
        
        for i in m.I_without_first:
            # CONSTR: delta_u_i lower bound
            m.constr_delta_u_i_ge.add(
                m.sent_u_i[u,i] + v_sent * m.delta_u_i[u,i] >= v_sent + users[u].get_n_buff_pkts_waited_i_TTIs(i) 
            )

            # CONSTR: delta_u_i upper bound
            m.constr_delta_u_i_le.add(
                m.sent_u_i[u,i] - (V_sent + e) * m.delta_u_i[u,i] <= users[u].get_n_buff_pkts_waited_i_TTIs(i)  - e
            )
        """
        # CONSTR: Average Buffer Latency intent
        m.constr_l_u_intent.add(
            users[u].get_sum_sent_pkts_ttis_waited() + sum(m.sent_u_i[u,i]*i for i in m.I)
            <= users[u].requirements["latency"] * (users[u].get_total_sent_pkts() + sum(m.sent_u_i[u,i] for i in m.I))
        )
        """
        """
        # CONSTR: Average Buffer Latency intent (modified 1)
        m.constr_l_u_intent.add(
            users[u].get_sum_sent_pkts_ttis_waited() + sum(m.sent_u_i[u,i]*i+remain_u_i[u,i]*(i+1) for i in m.I)
            <= users[u].requirements["latency"] * (users[u].get_total_sent_pkts() + sum(m.sent_u_i[u,i] + remain_u_i[u,i] for i in m.I))
        )
        """
        """
        # CONSTR: Average Buffer Latency intent (modified 2)
        m.constr_l_u_intent.add(
            sum(m.sent_u_i[u,i]*(i+1) for i in m.I)
            <= users[u].requirements["latency"] * sum(m.sent_u_i[u,i] for i in m.I)
        )
        """
        """
        # CONSTR: Average Buffer Latency intent (modified 3)
        m.constr_l_u_intent.add(
            users[u].get_sum_sent_pkts_ttis_waited() + sum(remain_u_i[u,i]*(i+1) for i in m.I)
            <= users[u].requirements["latency"] * (users[u].get_total_sent_pkts() + sum(remain_u_i[u,i] for i in m.I))
        )
        """
        # CONSTR: Average Buffer Latency intent (modified 4)
        for i in range(users[u].requirements["latency"], users[u].get_max_lat()):
            m.constr_l_u_intent.add(
                remain_u_i[u,i] <= 0
            )

        # Idea: add another avg buff lat constraint to guarantee the throughput for sending avg(buff[0:l_req]) pkts
        
        # CONSTR: maxover_u >= b_u_sup
        m.constr_maxover_u_ge_b_u_sup.add(
            m.MAXover_u[u] >= b_u_sup[u]
        )

        # CONSTR: maxover_u >= b_max
        m.constr_maxover_u_ge_b_max.add(
            m.MAXover_u[u] >= users[u].get_buffer_pkt_capacity()
        )
        
        # CONSTR: maxover_u <= b_u_sup
        m.constr_maxover_u_le_b_u_sup.add(
            m.MAXover_u[u] <= b_u_sup[u] + V_over * (1 - m.beta_u[u])
        )
        
        # CONSTR: maxover_u <= b_max
        m.constr_maxover_u_le_b_max.add(
            m.MAXover_u[u] <= users[u].get_buffer_pkt_capacity() + V_over * m.beta_u[u]
        )

        # CONSTR: Packet Loss Rate intent
        m.constr_p_u_intent.add(
            p_u[u] <= users[u].requirements["pkt_loss"]
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