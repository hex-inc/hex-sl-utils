#!/bin/sh

set -eu

REPO_URL="https://github.com/hex-inc/apache-ossie.git"
REF="ossie-hex-preview"
COMMAND="${1:-install}"
DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
PREVIEW_ROOT="${DATA_HOME}/ossie-preview"
PREVIEW_TOOL_DIR="${PREVIEW_ROOT}/tools"
PREVIEW_BIN_DIR="${PREVIEW_ROOT}/bin"
EXECUTABLES="ossie-hex ossie-databricks ossie-dbt honeydew-osi ossie-nvidia-gsf osi-omni ossie-orionbelt ossie-wisdom"
DISPATCHER_MARKER="# Managed by the Ossie preview installer."

usage() {
  printf "%s\n" \
    "Usage: install-ossie-hex [install|uninstall]" \
    "" \
    "Install is the default. Both commands operate on the complete" \
    "Vendor -> Ossie -> Hex converter suite."
}

require_uv() {
  if ! command -v uv >/dev/null 2>&1; then
    printf "%s\n" \
      "Error: uv is required:" \
      "https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 127
  fi
}

run_uv() {
  UV_TOOL_DIR="${PREVIEW_TOOL_DIR}" \
    UV_TOOL_BIN_DIR="${PREVIEW_BIN_DIR}" \
    uv "$@"
}

install_suite() {
  git_source="git+${REPO_URL}@${REF}"

  printf "Installing preview of Ossie converter suite from '%s'...\n" "${REF}"

  run_uv tool install \
    --quiet \
    --reinstall \
    --python 3.12 \
    --with "apache-ossie @ ${git_source}#subdirectory=python" \
    --with-executables-from "apache-ossie-databricks @ ${git_source}#subdirectory=converters/databricks" \
    --with-executables-from "apache-ossie-dbt @ ${git_source}#subdirectory=converters/dbt" \
    --with-executables-from "honeydew-osi @ ${git_source}#subdirectory=converters/honeydew" \
    --with-executables-from "apache-ossie-nvidia-gsf @ ${git_source}#subdirectory=converters/nvidia" \
    --with-executables-from "osi-omni @ ${git_source}#subdirectory=converters/omni" \
    --with-executables-from "apache-ossie-orionbelt @ ${git_source}#subdirectory=converters/orionbelt" \
    --with-executables-from "apache-ossie-wisdom @ ${git_source}#subdirectory=converters/wisdom" \
    "ossie-hex @ ${git_source}#subdirectory=converters/hex"

  for executable in ${EXECUTABLES}; do
    "${PREVIEW_BIN_DIR}/${executable}" --help >/dev/null
  done

  printf "Installed and verified all converters.\n"
}

uninstall_suite() {
  run_uv tool uninstall --all --quiet
  printf "Uninstalled Ossie preview converter suite.\n"
}

is_managed_dispatcher() {
  [ -f "${DISPATCHER_PATH}" ] &&
    grep -Fq "${DISPATCHER_MARKER}" "${DISPATCHER_PATH}"
}

check_dispatcher() {
  existing_dispatcher="$(command -v ossie-preview 2>/dev/null || true)"

  if [ -n "${existing_dispatcher}" ] &&
    [ "${existing_dispatcher}" != "${DISPATCHER_PATH}" ]; then
    printf "%s\n" \
      "Error: ossie-preview already resolves to ${existing_dispatcher}." \
      "This installer will not shadow an existing command." >&2
    exit 1
  fi

  if { [ -e "${DISPATCHER_PATH}" ] || [ -L "${DISPATCHER_PATH}" ]; } &&
    ! is_managed_dispatcher; then
    printf "%s\n" \
      "Error: ${DISPATCHER_PATH} already exists and is not managed by this installer." \
      "Move it out of the way before installing Ossie preview." >&2
    exit 1
  fi
}

install_dispatcher() {
  mkdir -p "${COMMAND_BIN_DIR}"
  dispatcher_tmp="${DISPATCHER_PATH}.tmp.$$"

  cat >"${dispatcher_tmp}" <<'DISPATCHER'
#!/bin/sh
# Managed by the Ossie preview installer.

set -eu

DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
PREVIEW_BIN="${DATA_HOME}/ossie-preview/bin"

usage() {
  printf "%s\n" \
    "Usage: ossie-preview <converter> [arguments...]" \
    "" \
    "Converters: hex, databricks, dbt, honeydew, nvidia, omni," \
    "            orionbelt, wisdom"
}

if [ "$#" -eq 0 ]; then
  usage >&2
  exit 2
fi

converter="$1"
shift

case "${converter}" in
  -h | --help | help)
    usage
    exit 0
    ;;
  hex) executable="ossie-hex" ;;
  databricks) executable="ossie-databricks" ;;
  dbt) executable="ossie-dbt" ;;
  honeydew) executable="honeydew-osi" ;;
  nvidia) executable="ossie-nvidia-gsf" ;;
  omni) executable="osi-omni" ;;
  orionbelt) executable="ossie-orionbelt" ;;
  wisdom) executable="ossie-wisdom" ;;
  *)
    printf "Error: unknown converter '%s'.\n" "${converter}" >&2
    usage >&2
    exit 2
    ;;
esac

exec "${PREVIEW_BIN}/${executable}" "$@"
DISPATCHER

  chmod 755 "${dispatcher_tmp}"
  mv -f "${dispatcher_tmp}" "${DISPATCHER_PATH}"
  printf "Installed command: %s\n" "${DISPATCHER_PATH}"
}

uninstall_dispatcher() {
  if is_managed_dispatcher; then
    rm -f "${DISPATCHER_PATH}"
    printf "Uninstalled ossie-preview command.\n"
  elif [ -e "${DISPATCHER_PATH}" ] || [ -L "${DISPATCHER_PATH}" ]; then
    printf "Left unrelated command untouched: %s\n" "${DISPATCHER_PATH}"
  else
    printf "ossie-preview command is not installed.\n"
  fi
}

case "${COMMAND}" in
  -h | --help | help)
    usage
    exit 0
    ;;
  install | uninstall)
    ;;
  *)
    printf "Error: unknown command '%s'.\n" "${COMMAND}" >&2
    usage >&2
    exit 2
    ;;
esac

if [ "$#" -gt 1 ]; then
  printf "Error: install and uninstall do not accept converter names.\n" >&2
  usage >&2
  exit 2
fi

require_uv
COMMAND_BIN_DIR="$(uv tool dir --bin)"
DISPATCHER_PATH="${COMMAND_BIN_DIR}/ossie-preview"

if [ "${COMMAND}" = "install" ]; then
  check_dispatcher
  install_suite
  install_dispatcher

  if ! command -v ossie-preview >/dev/null 2>&1; then
    printf "Run 'uv tool update-shell' and restart your shell to add %s to PATH.\n" \
      "${COMMAND_BIN_DIR}"
  fi

  printf "\nConvert an Ossie document to Hex with:\n"
  printf "  ossie-preview hex export -i model.ossie.yaml -o hex-output/\n"
else
  uninstall_suite
  uninstall_dispatcher
  rmdir "${PREVIEW_BIN_DIR}" "${PREVIEW_TOOL_DIR}" "${PREVIEW_ROOT}" 2>/dev/null || true
fi
