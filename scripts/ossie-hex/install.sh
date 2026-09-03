#!/bin/sh

set -eu

REPO_URL="https://github.com/hex-inc/apache-ossie.git"
REF="${OSSIE_HEX_REF:-ossie-hex-preview}"
COMMAND="${1:-install}"

usage() {
  echo "Usage: install-ossie-hex [install|uninstall]"
}

require_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is required: https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 127
  fi
}

install_ossie_hex() {
  git_source="git+${REPO_URL}@${REF}"

  printf "Installing ossie-hex from '%s'...\n" "${REF}"

  uv tool install \
    --force \
    --refresh \
    --python 3.11 \
    --with "apache-ossie @ ${git_source}#subdirectory=python" \
    "ossie-hex @ ${git_source}#subdirectory=converters/hex"

  bin_dir="$(uv tool dir --bin)"
  "${bin_dir}/ossie-hex" --help >/dev/null

  printf "\nossie-hex installed from '%s'.\n" "${REF}"

  if ! command -v ossie-hex >/dev/null 2>&1; then
    printf "Run 'uv tool update-shell' and restart your shell to add %s to PATH.\n" "${bin_dir}"
    printf "\nRun the converter directly:\n"
    printf "  %s/ossie-hex export -i model.yaml -o hex-project/\n" "${bin_dir}"
  else
    printf "\nRun the converter:\n"
    printf "  ossie-hex export -i model.yaml -o hex-project/\n"
  fi
}

uninstall_ossie_hex() {
  if uv tool list | grep -q '^ossie-hex '; then
    uv tool uninstall ossie-hex
    echo "ossie-hex uninstalled."
  else
    echo "ossie-hex is not installed."
  fi
}

require_uv

case "${COMMAND}" in
  install)
    install_ossie_hex
    ;;
  uninstall)
    uninstall_ossie_hex
    ;;
  -h | --help | help)
    usage
    ;;
  *)
    echo "Error: unknown command '${COMMAND}'." >&2
    usage >&2
    exit 2
    ;;
esac
