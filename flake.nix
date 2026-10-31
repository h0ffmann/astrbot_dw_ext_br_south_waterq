{
  description = "Development shell of astrbot_dw_ext_br_south_waterq";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSystem = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forEachSystem (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = [ pkgs.python312 pkgs.uv pkgs.just pkgs.git pkgs.ruff pkgs.unzip ];
            # uv installs the Python packages. It must use the Python of this shell.
            UV_PYTHON = "${pkgs.python312}/bin/python";
            UV_PYTHON_DOWNLOADS = "never";
            # The ruff wheel does not run on NixOS. "just" uses this binary.
            # Keep the version in requirements-dev.txt the same as this version.
            RUFF = "${pkgs.ruff}/bin/ruff";
            # Some wheels load this library.
            LD_LIBRARY_PATH = pkgs.lib.optionalString pkgs.stdenv.hostPlatform.isLinux
              (pkgs.lib.makeLibraryPath [ pkgs.stdenv.cc.cc ]);
          };
        });
    };
}
