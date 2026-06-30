===== 2-hop 打分(b0_prop 门上的 propagation-erosion + per-template)=====
# 编辑态 2-hop · n_pool=150
# [POOLED(template-unweighted)] n_b0_prop=48/150  hop_ES@budget={'B0': 0.32, 'B3': 0.513}
#   ★propagation-erosion B0→B3 = 0.188 [0.083, 0.292]  分解{'stays_new': 39, 'flips_to_old': 1, 'neither': 8}
#   (次/陈旧)revert 括号 0.021/0.021
# per-template(relation):
#   r=P27    n= 57 hop_ES@B0=0.474  b0_prop= 27  prop-eros=0.148 [0.037, 0.296]
#   r=P495   n= 26 hop_ES@B0=0.308  b0_prop=  8  prop-eros=0.25 [0.0, 0.625]
#   r=P136   n= 22 hop_ES@B0=0.273  b0_prop=  6  prop-eros=0.167 [0.0, 0.5]
#   r=P175   n=  6 hop_ES@B0=0.5  b0_prop=  3  prop-eros=0.0 [0.0, 0.0]
#   r=P176   n=  5 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P50    n=  5 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P170   n=  4 hop_ES@B0=0.25  b0_prop=  1  prop-eros=0.0 [0.0, 0.0]
#   r=P26    n=  4 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P413   n=  4 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P449   n=  3 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P178   n=  2 hop_ES@B0=1.0  b0_prop=  2  prop-eros=0.5 [0.0, 1.0]
#   r=P69    n=  2 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P112   n=  2 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P108   n=  1 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P40    n=  1 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P800   n=  1 hop_ES@B0=1.0  b0_prop=  1  prop-eros=1.0 [1.0, 1.0]
#   r=P159   n=  1 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P6     n=  1 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P641   n=  1 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P35    n=  1 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
#   r=P286   n=  1 hop_ES@B0=0.0  b0_prop=  0  (b0_prop 不足)
# → results/mh/score_2hop.json
→ 看 n_b0_prop(编辑 B0 传到 2-hop 的数;<40=bounded-null→可能要 32B)+ propagation-erosion B0→B3 + per-template。陈旧 revert 只作次要括号。预注册三结局见 depth-plan。
[root:why-aaai27]$ cat results/mh/score_2hop.json   # 或脚本末尾打印
{
  "pooled": {
    "label": "POOLED(template-unweighted)",
    "n_all": 150,
    "hop_ES_marginal": {
      "B0": 0.32,
      "B3": 0.513
    },
    "n_b0_prop": 48,
    "propagation_erosion_B0toB3": {
      "rate": 0.188,
      "ci": [
        0.083,
        0.292
      ],
      "decomp": {
        "stays_new": 39,
        "flips_to_old": 1,
        "neither": 8
      }
    },
    "stale_revert_bracket_B3": {
      "hop_RR": 0.021,
      "hop_RRs": 0.021,
      "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"
    }
  },
  "per_template": {
    "P27": {
      "label": "r=P27",
      "n_all": 57,
      "hop_ES_marginal": {
        "B0": 0.474,
        "B3": 0.737
      },
      "n_b0_prop": 27,
      "propagation_erosion_B0toB3": {
        "rate": 0.148,
        "ci": [
          0.037,
          0.296
        ],
        "decomp": {
          "stays_new": 23,
          "flips_to_old": 0,
          "neither": 4
        }
      },
      "stale_revert_bracket_B3": {
        "hop_RR": 0.0,
        "hop_RRs": 0.0,
        "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"
      }
    },
    "P495": {
      "label": "r=P495",
      "n_all": 26,
      "hop_ES_marginal": {
        "B0": 0.308,
        "B3": 0.577
      },
      "n_b0_prop": 8,
      "propagation_erosion_B0toB3": {
        "rate": 0.25,
        "ci": [
          0.0,
          0.625
        ],
        "decomp": {
          "stays_new": 6,
          "flips_to_old": 0,
          "neither": 2
        }
      },
      "stale_revert_bracket_B3": {
        "hop_RR": 0.0,
        "hop_RRs": 0.0,
        "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"
      }
    },
    "P136": {
      "label": "r=P136",
      "n_all": 22,
      "hop_ES_marginal": {
        "B0": 0.273,
        "B3": 0.455
      },
      "n_b0_prop": 6,
      "propagation_erosion_B0toB3": {
        "rate": 0.167,
        "ci": [
          0.0,
          0.5
        ],
        "decomp": {
          "stays_new": 5,
          "flips_to_old": 0,
          "neither": 1
        }
      },
      "stale_revert_bracket_B3": {
        "hop_RR": 0.0,
        "hop_RRs": 0.0,
        "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"
      }
    },
    "P175": {
      "label": "r=P175",
      "n_all": 6,
      "hop_ES_marginal": {
        "B0": 0.5,
        "B3": 0.5
      },
      "n_b0_prop": 3,
      "propagation_erosion_B0toB3": {
        "rate": 0.0,
        "ci": [
          0.0,
          0.0
        ],
        "decomp": {
          "stays_new": 3,
          "flips_to_old": 0,
          "neither": 0
        }
      },
      "stale_revert_bracket_B3": {
        "hop_RR": 0.0,
        "hop_RRs": 0.0,
        "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"
      }
    },
    "P176": {
      "label": "r=P176",
      "n_all": 5,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P50": {
      "label": "r=P50",
      "n_all": 5,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P170": {
      "label": "r=P170",
      "n_all": 4,
      "hop_ES_marginal": {
        "B0": 0.25,
        "B3": 0.5
      },
      "n_b0_prop": 1,
      "propagation_erosion_B0toB3": {
        "rate": 0.0,
        "ci": [
          0.0,
          0.0
        ],
        "decomp": {
          "stays_new": 1,
          "flips_to_old": 0,
          "neither": 0
        }
      },
      "stale_revert_bracket_B3": {
        "hop_RR": 0.0,
        "hop_RRs": 0.0,
        "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"
      }
    },
    "P26": {
      "label": "r=P26",
      "n_all": 4,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P413": {
      "label": "r=P413",
      "n_all": 4,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.25
      },
      "n_b0_prop": 0
    },
    "P449": {
      "label": "r=P449",
      "n_all": 3,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P178": {
      "label": "r=P178",
      "n_all": 2,
      "hop_ES_marginal": {
        "B0": 1.0,
        "B3": 0.5
      },
      "n_b0_prop": 2,
      "propagation_erosion_B0toB3": {
        "rate": 0.5,
        "ci": [
          0.0,
          1.0
        ],
        "decomp": {
          "stays_new": 1,
          "flips_to_old": 1,
          "neither": 0
        }
      },
      "stale_revert_bracket_B3": {
        "hop_RR": 0.5,
        "hop_RRs": 0.5,
        "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"
      }
    },
    "P69": {
      "label": "r=P69",
      "n_all": 2,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P112": {
      "label": "r=P112",
      "n_all": 2,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 1.0
      },
      "n_b0_prop": 0
    },
    "P108": {
      "label": "r=P108",
      "n_all": 1,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P40": {
      "label": "r=P40",
      "n_all": 1,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P800": {
      "label": "r=P800",
      "n_all": 1,
      "hop_ES_marginal": {
        "B0": 1.0,
        "B3": 0.0
      },
      "n_b0_prop": 1,
      "propagation_erosion_B0toB3": {
        "rate": 1.0,
        "ci": [
          1.0,
          1.0
        ],
        "decomp": {
          "stays_new": 0,
          "flips_to_old": 0,
          "neither": 1
        }
      },
      "stale_revert_bracket_B3": {
        "hop_RR": 0.0,
        "hop_RRs": 0.0,
        "_note": "对 MQuAKE 陈旧下游 gold,不领先/不入 abstract"
      }
    },
    "P159": {
      "label": "r=P159",
      "n_all": 1,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 1.0
      },
      "n_b0_prop": 0
    },
    "P6": {
      "label": "r=P6",
      "n_all": 1,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P641": {
      "label": "r=P641",
      "n_all": 1,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P35": {
      "label": "r=P35",
      "n_all": 1,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    },
    "P286": {
      "label": "r=P286",
      "n_all": 1,
      "hop_ES_marginal": {
        "B0": 0.0,
        "B3": 0.0
      },
      "n_b0_prop": 0
    }
  },
  "_estimand": "propagation-erosion = 编辑在 B0 传到 2-hop 的 case 中,B3 思考后丢失 hop_answer_new 的比例(配对);陈旧 revert 仅作次要括号。"