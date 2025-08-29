{
  description = "Heyu - Python implementation of X10 home automation controller";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          pyserial
          click
          pydantic
          pytest
          pytest-cov
          pytest-mock
          black
          isort
          mypy
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python and package management
            uv
            pythonEnv
            
            # Development tools
            git
            pre-commit
            
            # Hardware access (for serial ports)
            pkg-config
            
            # Documentation
            mdbook
          ];

          shellHook = ''
            echo "🏠 Heyu Development Environment"
            echo "Python: $(python --version)"
            echo "UV: $(uv --version)"
            echo ""
            echo "Quick start:"
            echo "  uv sync                # Install dependencies"
            echo "  uv run pytest         # Run tests"
            echo "  uv run heyu info       # Run heyu info command"
            echo ""
            
            # Set up pre-commit hooks if not already done
            if [ ! -f .git/hooks/pre-commit ]; then
              echo "Setting up pre-commit hooks..."
              pre-commit install
            fi
            
            # Ensure user can access serial ports (Linux)
            if [ -d /dev/serial ]; then
              echo "Note: You may need to add your user to the 'dialout' group for serial port access:"
              echo "  sudo usermod -a -G dialout \$USER"
            fi
          '';
          
          # Environment variables
          PYTHONPATH = ".";
        };

        packages.default = pkgs.python311Packages.buildPythonApplication {
          pname = "heyu";
          version = "3.0.0";
          
          src = ./.;
          format = "pyproject";
          
          nativeBuildInputs = with pkgs.python311Packages; [
            hatchling
          ];
          
          propagatedBuildInputs = with pkgs.python311Packages; [
            pyserial
            click
            pydantic
          ];
          
          checkInputs = with pkgs.python311Packages; [
            pytest
            pytest-cov
            pytest-mock
          ];
          
          pythonImportsCheck = [ "heyu" ];
          
          meta = with pkgs.lib; {
            description = "Python implementation of X10 home automation controller";
            homepage = "https://github.com/heyu-py/heyu";
            license = licenses.gpl3Plus;
            maintainers = [ ];
            platforms = platforms.unix;
          };
        };
      });
}