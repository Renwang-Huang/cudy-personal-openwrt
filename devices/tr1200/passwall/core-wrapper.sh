#!/bin/sh
export GOMAXPROCS="${GOMAXPROCS:-1}"
export GOMEMLIMIT="${GOMEMLIMIT:-24MiB}"
export GOGC="${GOGC:-50}"
exec /usr/libexec/sing-box-cudy-lite "$@"
