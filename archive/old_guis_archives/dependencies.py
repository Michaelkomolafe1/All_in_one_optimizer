def install_dependencies():
    try:
        import pulp
    except ImportError:
        print("Installing PuLP for MILP optimization...")
        import subprocess
        subprocess.check_call(["pip", "install", "pulp"])

    try:
        import PyQt5
    except ImportError:
        print("Installing PyQt5 for GUI...")
        import subprocess
        subprocess.check_call(["pip", "install", "PyQt5"])

# Call this at the start of your main script if you want runtime dependency checking
if __name__ == "__main__":
    install_dependencies()