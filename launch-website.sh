#!/bin/bash

# LawyerFactory Website Launcher
# Comprehensive script to launch, troubleshoot, and manage the LawyerFactory web interfaces

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_PORT=8000
ENHANCED_FACTORY_PATH="src/lawyerfactory/phases/04_human_review/ui/enhanced_factory.html"
SIMPLE_FACTORY_PATH="apps/ui/templates/factory.html"
LOG_FILE="$SCRIPT_DIR/website-launch.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[LAUNCHER]${NC} $1"
}

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check system requirements
check_requirements() {
    print_header "Checking system requirements..."

    # Check for Python (required for HTTP server)
    if command_exists python3; then
        PYTHON_CMD="python3"
        print_status "Python 3 found"
    elif command_exists python; then
        PYTHON_CMD="python"
        print_status "Python found"
    else
        print_error "Python is required but not found. Please install Python 3."
        exit 1
    fi

    # Check for Node.js (optional, for enhanced features)
    if command_exists node; then
        print_status "Node.js found (optional, for enhanced features)"
    else
        print_warning "Node.js not found. Some features may be limited."
    fi

    # Check for curl (for health checks)
    if command_exists curl; then
        print_status "curl found (for health checks)"
    else
        print_warning "curl not found. Health checks will be skipped."
    fi
}

# Find available port
find_available_port() {
    local port=$1
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        port=$((port + 1))
    done
    echo $port
}

# Get file size for comparison
get_file_size() {
    if [[ -f "$1" ]]; then
        stat -f%z "$1" 2>/dev/null || stat -c%s "$1" 2>/dev/null || echo "0"
    else
        echo "0"
    fi
}

# Compare HTML files and recommend which to use
analyze_html_files() {
    print_header "Analyzing HTML files..."

    local enhanced_size=$(get_file_size "$ENHANCED_FACTORY_PATH")
    local simple_size=$(get_file_size "$SIMPLE_FACTORY_PATH")

    echo "Enhanced Factory ($ENHANCED_FACTORY_PATH): $(numfmt --to=iec-i --suffix=B $enhanced_size)"
    echo "Simple Factory ($SIMPLE_FACTORY_PATH): $(numfmt --to=iec-i --suffix=B $simple_size)"

    if [[ $enhanced_size -gt $simple_size ]]; then
        print_status "Enhanced Factory appears to be more feature-rich"
        RECOMMENDED_FILE="$ENHANCED_FACTORY_PATH"
    else
        print_status "Simple Factory appears to be more lightweight"
        RECOMMENDED_FILE="$SIMPLE_FACTORY_PATH"
    fi
}

# Start Python HTTP server
start_python_server() {
    local port=$1
    local html_file=$2
    local serve_dir=$(dirname "$html_file")

    print_header "Starting Python HTTP server..."
    print_status "Serving: $html_file"
    print_status "Directory: $serve_dir"
    print_status "Port: $port"

    cd "$serve_dir"

    # Start server in background
    $PYTHON_CMD -m http.server $port > "$LOG_FILE" 2>&1 &
    SERVER_PID=$!

    cd "$SCRIPT_DIR"

    # Wait a moment for server to start
    sleep 2

    # Check if server is running
    if kill -0 $SERVER_PID 2>/dev/null; then
        print_status "Server started successfully (PID: $SERVER_PID)"
        echo "Access your website at: http://localhost:$port/$(basename "$html_file")"
        return 0
    else
        print_error "Failed to start server"
        return 1
    fi
}

# Health check function
health_check() {
    local url=$1
    local max_attempts=10
    local attempt=1

    print_header "Performing health check..."

    while [[ $attempt -le $max_attempts ]]; do
        if curl -s --head "$url" > /dev/null 2>&1; then
            print_status "Health check passed: $url"
            return 0
        fi

        print_warning "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 1
        ((attempt++))
    done

    print_error "Health check failed after $max_attempts attempts"
    return 1
}

# Display server information
display_server_info() {
    local port=$1
    local html_file=$2

    echo ""
    print_header "=== SERVER INFORMATION ==="
    echo "PID: $SERVER_PID"
    echo "Port: $port"
    echo "HTML File: $html_file"
    echo "URL: http://localhost:$port/$(basename "$html_file")"
    echo "Log File: $LOG_FILE"
    echo ""
    echo "To stop the server, press Ctrl+C or run: kill $SERVER_PID"
    echo ""
}

# Cleanup function
cleanup() {
    if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
        print_warning "Stopping server (PID: $SERVER_PID)"
        kill "$SERVER_PID" 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Main function
main() {
    local port=$DEFAULT_PORT
    local html_file=""
    local auto_select=false

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                port="$2"
                shift 2
                ;;
            -f|--file)
                html_file="$2"
                shift 2
                ;;
            --enhanced)
                html_file="$ENHANCED_FACTORY_PATH"
                shift
                ;;
            --simple)
                html_file="$SIMPLE_FACTORY_PATH"
                shift
                ;;
            --auto)
                auto_select=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    print_header "LawyerFactory Website Launcher"
    log "Launcher started with arguments: $*"

    # Check requirements
    check_requirements

    # Analyze HTML files
    analyze_html_files

    # Auto-select file if requested
    if [[ "$auto_select" == true ]] && [[ -z "$html_file" ]]; then
        html_file="$RECOMMENDED_FILE"
        print_status "Auto-selected: $html_file"
    fi

    # Validate HTML file selection
    if [[ -z "$html_file" ]]; then
        print_error "No HTML file specified. Use --enhanced, --simple, or --file option."
        echo ""
        show_help
        exit 1
    fi

    if [[ ! -f "$html_file" ]]; then
        print_error "HTML file not found: $html_file"
        exit 1
    fi

    # Find available port
    port=$(find_available_port "$port")
    print_status "Using port: $port"

    # Start the server
    if start_python_server "$port" "$html_file"; then
        # Perform health check
        local url="http://localhost:$port/$(basename "$html_file")"
        if command_exists curl; then
            health_check "$url"
        fi

        # Display server information
        display_server_info "$port" "$html_file"

        # Wait for server to be stopped
        print_status "Server is running... Press Ctrl+C to stop."
        wait $SERVER_PID
    else
        print_error "Failed to start server"
        exit 1
    fi
}

# Help function
show_help() {
    cat << EOF
LawyerFactory Website Launcher

USAGE:
    $0 [OPTIONS]

OPTIONS:
    -p, --port PORT          Specify port number (default: $DEFAULT_PORT)
    -f, --file FILE          Specify HTML file to serve
    --enhanced               Use enhanced factory interface
    --simple                 Use simple factory interface
    --auto                   Auto-select recommended interface
    -h, --help               Show this help message

EXAMPLES:
    $0 --enhanced                    # Launch enhanced interface
    $0 --simple                      # Launch simple interface
    $0 --auto                        # Auto-select best interface
    $0 --file /path/to/file.html     # Launch specific file
    $0 --enhanced --port 8080        # Launch on specific port

HTML FILES:
    Enhanced: $ENHANCED_FACTORY_PATH
    Simple:   $SIMPLE_FACTORY_PATH

TROUBLESHOOTING:
    - Check $LOG_FILE for detailed logs
    - Ensure ports are not already in use
    - Verify HTML files exist and are readable
    - Check firewall settings if accessing remotely

EOF
}

# Run main function with all arguments
main "$@"