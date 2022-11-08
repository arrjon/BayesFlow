# Copyright (c) 2022 The BayesFlow Developers

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np

import pytest

from bayesflow.coupling_networks import AffineCouplingLayer
from bayesflow.helper_functions import build_meta_dict
from bayesflow.default_settings import DEFAULT_SETTING_INVERTIBLE_NET


@pytest.mark.parametrize("input_dim", [2, 5])
@pytest.mark.parametrize("condition_dim", [8, None])
@pytest.mark.parametrize("units", [16, 8])
@pytest.mark.parametrize("spec_norm", [True, False])
@pytest.mark.parametrize("use_perm", [True, False])
@pytest.mark.parametrize("use_act_norm", [True, False])
def test_coupling_layer(input_dim, condition_dim, units, spec_norm, use_perm, use_act_norm):
    """Tests the `CouplingLayer` instance with various configurations."""

    # Create settings dictionaries and network
    dense_net_settings = {
        't_args': {
            'dense_args': dict(units=units, kernel_initializer='glorot_uniform', activation='elu'),
            'n_dense': 2,
            'spec_norm': spec_norm
        },
        's_args': {
            'dense_args': dict(units=units, kernel_initializer='glorot_uniform', activation='elu'),
            'n_dense': 1,
            'spec_norm': spec_norm
        },
    }
    meta = build_meta_dict(user_dict={
        'coupling_settings': dense_net_settings,
        'use_permutation': use_perm,
        'use_act_norm': use_act_norm,
        'n_params': input_dim
    },
    default_setting=DEFAULT_SETTING_INVERTIBLE_NET)

    network = AffineCouplingLayer(meta)

    # Create randomized input and output conditions
    batch_size = np.random.randint(low=1, high=32)
    inp = np.random.normal(size=(batch_size, input_dim)).astype(np.float32)
    if condition_dim is None:
        condition = None
    else:
        condition = np.random.normal(size=(batch_size, condition_dim)).astype(np.float32)

    # Forward and inverse pass
    z, ldj = network(inp, condition)
    inp_rec = network(z, condition, inverse=True).numpy()

    # Test attributes
    if use_perm:
        assert network.permutation is not None
    if use_act_norm:
        assert network.act_norm is not None
    # Test invertibility
    assert np.allclose(inp, inp_rec, atol=1e6)
    # Test shapes (bijectivity)
    assert z.shape[0] == inp.shape[0] and z.shape[1] == inp.shape[1]
    assert ldj.shape[0] == inp.shape[0]
