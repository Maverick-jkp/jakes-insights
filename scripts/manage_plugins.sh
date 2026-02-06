#!/bin/bash

# Claude Code Plugin Manager
# Easy access to Claude plugins

PLUGIN_DIR="$HOME/.claude/plugins"
OFFICIAL_PLUGINS="$PLUGIN_DIR/marketplaces/claude-plugins-official/plugins"
INSTALLED_JSON="$PLUGIN_DIR/installed_plugins.json"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    echo "Usage: ./scripts/manage_plugins.sh [command]"
    echo ""
    echo "Commands:"
    echo "  list, ls       - List all installed plugins"
    echo "  info           - Show detailed plugin information"
    echo "  path           - Show plugin directory paths"
    echo "  open           - Open plugin directory in Finder"
    echo "  help           - Show this help message"
}

list_plugins() {
    echo -e "${BLUE}=== Installed Claude Plugins ===${NC}\n"

    if [ -f "$INSTALLED_JSON" ]; then
        echo -e "${GREEN}From installed_plugins.json:${NC}"
        cat "$INSTALLED_JSON" | grep '@claude-plugins-official' | sed 's/"//g' | sed 's/,//g' | awk -F'@' '{print "  - " $1}'
    fi

    echo ""
    echo -e "${GREEN}Available in marketplace:${NC}"
    if [ -d "$OFFICIAL_PLUGINS" ]; then
        ls -1 "$OFFICIAL_PLUGINS" | while read plugin; do
            echo "  - $plugin"
        done
    fi
}

show_info() {
    echo -e "${BLUE}=== Plugin Information ===${NC}\n"

    if [ -f "$INSTALLED_JSON" ]; then
        echo -e "${GREEN}Installed plugins with versions:${NC}"
        cat "$INSTALLED_JSON" | python3 -m json.tool 2>/dev/null || cat "$INSTALLED_JSON"
    fi
}

show_paths() {
    echo -e "${BLUE}=== Plugin Paths ===${NC}\n"
    echo -e "${GREEN}Main plugin directory:${NC}"
    echo "  $PLUGIN_DIR"
    echo ""
    echo -e "${GREEN}Official plugins marketplace:${NC}"
    echo "  $OFFICIAL_PLUGINS"
    echo ""
    echo -e "${GREEN}Installed plugins config:${NC}"
    echo "  $INSTALLED_JSON"
    echo ""
    echo -e "${GREEN}Project symlink:${NC}"
    echo "  $(pwd)/.claude/plugins-link/system-plugins"
}

open_finder() {
    if [ -d "$PLUGIN_DIR" ]; then
        open "$PLUGIN_DIR"
        echo -e "${GREEN}Opened plugin directory in Finder${NC}"
    else
        echo -e "${YELLOW}Plugin directory not found: $PLUGIN_DIR${NC}"
    fi
}

# Main command router
case "${1:-help}" in
    list|ls)
        list_plugins
        ;;
    info)
        show_info
        ;;
    path|paths)
        show_paths
        ;;
    open)
        open_finder
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${YELLOW}Unknown command: $1${NC}\n"
        show_help
        exit 1
        ;;
esac
