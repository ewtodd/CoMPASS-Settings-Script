{
  description = "Python environment for extracting CoMPASS settings.";

  inputs = { nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05"; };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux"; # Change to your system
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs;
          [
            (python3.withPackages
              (python-pkgs: with python-pkgs; [ pandas tables ]))
          ];
        shellHook = "";
      };
    };
}
