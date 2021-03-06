#!/usr/bin/env python3
#
#  Copyright (c) 2019, The OpenThread Authors.
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#  3. Neither the name of the copyright holder nor the
#     names of its contributors may be used to endorse or promote products
#     derived from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
#  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#  IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#  ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
#  LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#  CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#  SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#  CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#  ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#
import logging
import os
import subprocess
import sys
from typing import Callable, Union

from pktverify.addrs import EthAddr, ExtAddr, Ipv6Addr
from pktverify.bytes import Bytes
from pktverify.null_field import nullField


def make_filter_func(func: Union[str, Callable], **vars) -> Callable:
    """
    Convert the filter to a callable function if it's a string.

    :param func: The filter string or callable.
    :param vars: The variables.
    :return: The filter callable.
    """
    if isinstance(func, str):
        # if func is a string, compile it to a function
        func = func.format_map({k: repr(v) for k, v in vars.items()}).strip()
        print("\t%s" % func, file=sys.stderr)
        code = compile('(\n' + func + '\n)', func, "eval")

        def func(p):
            return eval(
                code, None, {
                    'p': p,
                    'coap': p.coap,
                    'wpan': p.wpan,
                    'mle': p.mle,
                    'ipv6': p.ipv6,
                    'lowpan': p.lowpan,
                    'eth': p.eth,
                    'icmpv6': p.icmpv6,
                    'udp': p.udp,
                    'thread_bl': p.thread_bl,
                    'thread_meshcop': p.thread_meshcop,
                    'Bytes': Bytes,
                    'ExtAddr': ExtAddr,
                    'Ipv6Addr': Ipv6Addr,
                    'EthAddr': EthAddr,
                    'thread_nm': p.thread_nm,
                    'thread_nwd': p.thread_nwd,
                    'null': nullField,
                })
    else:
        assert not vars, 'can not provide vars for non-str filter: %r %r' % (func, vars)

    assert callable(func)
    return func


def _install_travis_thread_wireshark():
    logging.info("downloading thread-wireshark from https://github.com/openthread/wireshark/releases ...")

    download_url = 'https://github.com/openthread/wireshark/releases/download/ot-pktverify-20200727/thread-wireshark.tar.gz'
    save_file = '/tmp/thread-wireshark.tar.gz'

    subprocess.check_call(f'curl -L {download_url} -o {save_file}', shell=True)
    subprocess.check_call(f'tar -C /tmp -xvzf {save_file}', shell=True)
    assert os.path.isdir('/tmp/thread-wireshark')


def _setup_wireshark_disabled_protos():
    home = os.environ['HOME']
    wireshark_config_dir = os.path.join(home, '.config', 'wireshark')
    os.makedirs(wireshark_config_dir, exist_ok=True)
    disabled_protos_path = os.path.join(wireshark_config_dir, 'disabled_protos')
    # read current disabled protos
    try:
        with open(disabled_protos_path, 'rt') as fd:
            disabled_protos = set(l.strip() for l in fd if l.strip() != '')
    except FileNotFoundError:
        disabled_protos = set()

    old_disabled_protos_num = len(disabled_protos)
    disabled_protos.add('lwm')
    disabled_protos.add('prp')
    disabled_protos.add('stcsig')
    disabled_protos.add('transum')
    disabled_protos.add('zbee_nwk')
    disabled_protos.add('zbee_nwk_gp')

    if len(disabled_protos) > old_disabled_protos_num:
        logging.info(f"set disabled_protos = {' '.join(disabled_protos)}")
        with open(disabled_protos_path, 'wt') as fd:
            fd.write('\n'.join(sorted(disabled_protos)))
            fd.write('\n')


def get_wireshark_dir() -> str:
    """
    :return: The path to wireshark directory.
    """
    dir = '/tmp/thread-wireshark'
    if not os.path.exists(dir):
        _install_travis_thread_wireshark()

    _setup_wireshark_disabled_protos()

    return dir


def which_tshark() -> str:
    """
    :return: The path to `tshark` executable.
    """
    return os.path.join(get_wireshark_dir(), 'tshark')


def which_dumpcap() -> str:
    """
    :return: The path to `dumpcap` executable.
    """
    return os.path.join(get_wireshark_dir(), 'dumpcap')


def which_mergecap() -> str:
    """
    :return: The path to `mergecap` executable.
    """
    return os.path.join(get_wireshark_dir(), 'mergecap')
