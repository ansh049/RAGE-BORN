#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
#  RAGE Installer — AI-Powered Terminal Agent
#  Usage: curl -fsSL https://raw.githubusercontent.com/YADAV1825/rage/main/install.sh | bash
# ═══════════════════════════════════════════════════════════════════════════════

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
ORANGE='\033[0;33m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

echo ""
echo -e "${RED}██████╗   █████╗   ██████╗  ███████╗${NC}"
echo -e "${ORANGE}██╔══██╗ ██╔══██╗ ██╔════╝  ██╔════╝${NC}"
echo -e "${YELLOW}██████╔╝ ███████║ ██║  ███╗ █████╗${NC}"
echo -e "${ORANGE}██╔══██╗ ██╔══██║ ██║   ██║ ██╔══╝${NC}"
echo -e "${RED}██║  ██║ ██║  ██║ ╚██████╔╝ ███████╗${NC}"
echo -e "${RED}╚═╝  ╚═╝ ╚═╝  ╚═╝  ╚═════╝  ╚══════╝${NC}"
echo ""
echo -e "${BOLD}⚡ RAGE Installer${NC} — AI-Powered Terminal Agent"
echo ""

# ── Check Python ──────────────────────────────────────────────────────────────
echo -e "${DIM}Checking Python...${NC}"

PYTHON=""
for cmd in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$cmd" &> /dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}✗ Python 3.10+ is required but not found.${NC}"
    echo -e "  Install Python 3.10+ and try again."
    exit 1
fi

echo -e "${GREEN}✓${NC} Found $($PYTHON --version)"

# ── Check pip ─────────────────────────────────────────────────────────────────
echo -e "${DIM}Checking pip...${NC}"

if ! $PYTHON -m pip --version &> /dev/null; then
    echo -e "${RED}✗ pip not found. Installing...${NC}"
    $PYTHON -m ensurepip --upgrade 2>/dev/null || {
        echo -e "${RED}✗ Could not install pip. Please install it manually.${NC}"
        exit 1
    }
fi

echo -e "${GREEN}✓${NC} pip available"

# ── Install RAGE ──────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}Installing RAGE...${NC}"

# Clone or download
INSTALL_DIR="$HOME/.rage/source"
mkdir -p "$HOME/.rage"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${DIM}Updating existing installation...${NC}"
    cd "$INSTALL_DIR"
    git pull --quiet 2>/dev/null || true
else
    echo -e "${DIM}Downloading RAGE...${NC}"
    if command -v git &> /dev/null; then
        git clone --quiet https://github.com/YADAV1825/rage.git "$INSTALL_DIR" 2>/dev/null || {
            echo -e "${YELLOW}⚠ Git clone failed. Trying pip install...${NC}"
            $PYTHON -m pip install --user rage-cli 2>/dev/null || {
                echo -e "${RED}✗ Installation failed. Please install manually:${NC}"
                echo -e "  ${DIM}pip install rage-cli${NC}"
                exit 1
            }
            echo -e "${GREEN}✓ Installed via pip${NC}"
            INSTALL_DIR=""
        }
    fi
fi

if [ -n "$INSTALL_DIR" ] && [ -d "$INSTALL_DIR" ]; then
    cd "$INSTALL_DIR"
    $PYTHON -m pip install --user -e . --quiet 2>/dev/null || {
        $PYTHON -m pip install --user -e . 2>&1
    }
fi

# ── Create directories ───────────────────────────────────────────────────────
echo -e "${DIM}Setting up directories...${NC}"
mkdir -p "$HOME/.rage/logs"
mkdir -p "$HOME/.rage/browser_profile"

# ── Verify installation ──────────────────────────────────────────────────────
echo ""

if command -v rage &> /dev/null; then
    echo -e "${GREEN}${BOLD}✓ RAGE installed successfully!${NC}"
elif $PYTHON -m rage --help &> /dev/null 2>&1; then
    echo -e "${GREEN}${BOLD}✓ RAGE installed successfully!${NC}"
    echo -e "${YELLOW}⚠ 'rage' command not in PATH. You can run with: python -m rage${NC}"
    
    # Try to add to PATH
    USER_BIN="$HOME/.local/bin"
    if [ -d "$USER_BIN" ]; then
        echo -e "${DIM}Adding to PATH via ~/.local/bin...${NC}"
        # Check if rage script exists there
        if [ ! -f "$USER_BIN/rage" ]; then
            echo '#!/usr/bin/env bash' > "$USER_BIN/rage"
            echo "exec $PYTHON -m rage \"\$@\"" >> "$USER_BIN/rage"
            chmod +x "$USER_BIN/rage"
            echo -e "${GREEN}✓ Created rage launcher at $USER_BIN/rage${NC}"
        fi
    fi
else
    echo -e "${RED}✗ Installation verification failed.${NC}"
    echo -e "  Try: ${DIM}$PYTHON -m pip install -e .${NC} in the RAGE directory."
    exit 1
fi

echo ""
echo -e "${BOLD}Getting started:${NC}"
echo -e "  ${GREEN}rage${NC}                    Start interactive mode"
echo -e "  ${GREEN}rage \"install docker\"${NC}   Run a direct command"
echo -e "  ${GREEN}rage --help${NC}             Show help"
echo ""
echo -e "${DIM}⚡ First run will ask for your API key.${NC}"
echo ""
