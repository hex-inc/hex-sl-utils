#!/bin/sh

set -eu

# Full commits only. The same Hex commit supplies the converter and utilities.
# Overrides support testing candidate commits and local Git clones.
OSSIE_REPO_URL="${OSSIE_PREVIEW_OSSIE_REPO_URL:-https://github.com/hex-inc/apache-ossie.git}"
OSSIE_REV="${OSSIE_PREVIEW_OSSIE_REV:-8b1b894c90b57d9727ee8153893ec7fd35124959}"
HEX_REPO_URL="${OSSIE_PREVIEW_HEX_REPO_URL:-https://github.com/hex-inc/hex-sl-utils.git}"
HEX_REV="${OSSIE_PREVIEW_HEX_REV:-368a7710c6d1fb9ee4127caa7f7eeedba1113e83}"
COMMAND="${1:-install}"
DATA_HOME="${XDG_DATA_HOME:-${HOME}/.local/share}"
PREVIEW_ROOT="${DATA_HOME}/ossie-preview"
PREVIEW_TOOL_DIR="${PREVIEW_ROOT}/tools"
PREVIEW_BIN_DIR="${PREVIEW_ROOT}/bin"
EXECUTABLES="ossie-hex ossie-databricks ossie-dbt ossie-honeydew ossie-nvidia-gsf ossie-omni ossie-orionbelt ossie-wisdom"
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

require_commit() {
  pin_name="$1"
  pin_value="$2"
  case "${pin_value}" in
    *[!0-9a-f]* | "")
      printf "Error: %s must be a full lowercase Git commit SHA.\n" "${pin_name}" >&2
      exit 1
      ;;
  esac
  if [ "${#pin_value}" -ne 40 ]; then
    printf "Error: %s must be a full lowercase Git commit SHA.\n" "${pin_name}" >&2
    exit 1
  fi
}

install_suite() {
  require_commit OSSIE_REV "${OSSIE_REV}"
  require_commit HEX_REV "${HEX_REV}"
  ossie_source="git+${OSSIE_REPO_URL}@${OSSIE_REV}"
  hex_source="git+${HEX_REPO_URL}@${HEX_REV}"

  printf "Installing preview: Hex %s, Ossie %s...\n" "${HEX_REV}" "${OSSIE_REV}"

  run_uv tool install \
    --quiet \
    --reinstall \
    --python 3.12 \
    --with "apache-ossie @ ${ossie_source}#subdirectory=python" \
    --with "hex-sl-utils @ ${hex_source}#subdirectory=packages/hex-sl-utils" \
    --with-executables-from "apache-ossie-databricks @ ${ossie_source}#subdirectory=converters/databricks/python" \
    --with-executables-from "apache-ossie-dbt @ ${ossie_source}#subdirectory=converters/dbt" \
    --with-executables-from "apache-ossie-honeydew @ ${ossie_source}#subdirectory=converters/honeydew" \
    --with-executables-from "apache-ossie-nvidia-gsf @ ${ossie_source}#subdirectory=converters/nvidia" \
    --with-executables-from "ossie-omni @ ${ossie_source}#subdirectory=converters/omni" \
    --with-executables-from "apache-ossie-orionbelt @ ${ossie_source}#subdirectory=converters/orionbelt" \
    --with-executables-from "apache-ossie-wisdom @ ${ossie_source}#subdirectory=converters/wisdom" \
    "ossie-hex @ ${hex_source}#subdirectory=packages/ossie-hex"

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
  honeydew) executable="ossie-honeydew" ;;
  nvidia) executable="ossie-nvidia-gsf" ;;
  omni) executable="ossie-omni" ;;
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
