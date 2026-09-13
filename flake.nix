{
  description = "Pinned usdAeco family gate";
  inputs = {
    core.url = "github:criad-com/usdaeco-core?ref=v0.9.5";
    core.flake = false;
    axis.url = "github:criad-com/usdaeco-axis?ref=v0.1.5";
    axis.flake = false;
    toolchain.url = "github:criad-com/usdaeco-toolchain?ref=v0.3.10";
    buildup.url = "github:criad-com/usdaeco-buildup?ref=v0.2.5";
    buildup.flake = false;
    wall.url = "github:criad-com/usdaeco-wall?ref=v0.2.5";
    wall.flake = false;
    pipe.url = "github:criad-com/usdaeco-pipe?ref=v0.2.5";
    pipe.flake = false;
    cctv.url = "github:criad-com/usdaeco-cctv?ref=v0.5.6";
    cctv.flake = false;
    cctv-exec.url = "github:criad-com/usdaeco-cctv-exec?ref=v0.2.4";
    cctv-exec.flake = false;
    sync.url = "github:criad-com/usdaeco-sync?ref=v0.5.5";
    sync.flake = false;
    ifc.url = "github:criad-com/usdaeco-ifc?ref=v0.2.3";
    ifc.flake = false;
    bonsai.url = "github:criad-com/usdaeco-bonsai?ref=v0.1.6";
    bonsai.flake = false;
    revit.url = "github:criad-com/usdaeco-revit?ref=v0.1.5";
    revit.flake = false;
    datacentre.url = "github:criad-com/usdaeco-datacentre?ref=v0.4.9";
    datacentre.flake = false;
    plan.url = "github:criad-com/usdaeco-plan?ref=v0.1.4";
    plan.flake = false;
    compliance.url = "github:criad-com/usdaeco-compliance?ref=v0.1.3";
    compliance.flake = false;
    repeat.url = "github:criad-com/usdaeco-repeat?ref=v0.2.1";
    repeat.flake = false;
    clash.url = "github:criad-com/usdaeco-clash?ref=v0.2.3";
    clash.flake = false;
    solid.url = "github:criad-com/usdaeco-solid?ref=v0.1.5";
    solid.flake = false;
    nixpkgs.follows = "toolchain/nixpkgs";
  };
  outputs = { self, nixpkgs, toolchain, ... }@inputs:
    let
      eachSystem = nixpkgs.lib.genAttrs [ "aarch64-darwin" "x86_64-linux" ];
      forSystem = system:
        let
          kit = toolchain.lib.forSystem system;
          pkgs = nixpkgs.legacyPackages.${system};
          core = kit.buildCodelessSchema { name = "usdAeco"; src = inputs.core; };
          axis = kit.buildCodelessSchema { name = "usdAecoAxis"; src = inputs.axis; deps = [ core ]; };
          buildup = kit.buildCodelessSchema { name = "usdAecoBuildUp"; src = inputs.buildup; deps = [ core ]; };
          wall = kit.buildCodelessSchema { name = "usdAecoWall"; src = inputs.wall; deps = [ core axis buildup ]; };
          pipe = kit.buildCodelessSchema { name = "usdAecoPipe"; src = inputs.pipe; deps = [ core axis ]; };
          cctv = kit.buildCodelessSchema { name = "usdAecoCctv"; src = inputs.cctv; deps = [ core ]; };
          sync = kit.buildCodelessSchema { name = "usdAecoSync"; src = inputs.sync; deps = [ core axis ]; };
          pluginSet = kit.pluginSet { plugins = [ core axis buildup wall pipe cctv sync ]; };
        in { inherit kit pkgs pluginSet; };
    in {
      packages = eachSystem (system: let p = forSystem system; in {
        default = p.pluginSet;
        inherit (p) pluginSet;
      });
      checks = eachSystem (system: let p = forSystem system; in {
        registry = p.pkgs.runCommand "usdaeco-family-registry" {
          nativeBuildInputs = [ p.kit.pythonEnv ];
        } ''
          export PXR_PLUGINPATH_NAME=${p.pluginSet}
          env -u PYTHONPATH python - <<'PYTHON'
          from pxr import Plug, Usd
          expected = {'usdAeco','usdAecoAxis','usdAecoBuildUp','usdAecoWall','usdAecoPipe','usdAecoCctv','usdAecoSync'}
          actual = {p.name for p in Plug.Registry().GetAllPlugins() if p.name.startswith('usdAeco') and not p.name.endswith('Validators')}
          assert actual == expected
          for name in ('AecoAxisAPI','AecoBuildUpAPI','AecoWallAPI','AecoPipeAPI','AecoCctvSensorAPI','AecoHostBindingAPI'):
              assert Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(name)
          assert Usd.SchemaRegistry().FindAppliedAPIPrimDefinition('AecoAxisAPI').GetPropertyMetadata('aeco:axis:length','aecoDerived') is True
          PYTHON
          mkdir -p "$out"
        '';
        structure = p.pkgs.runCommand "usdaeco-scenarios-structure" {
          nativeBuildInputs = [ p.kit.pythonEnv p.pkgs.git ];
        } ''
          export TOOLCHAIN_DIR=${toolchain}
          env -u PYTHONPATH python ${self}/check.py --structure-only
          mkdir -p "$out"
        '';
      });
      devShells = eachSystem (system: let p = forSystem system; in {
        default = p.pkgs.mkShell {
          packages = [ p.kit.pythonEnv p.kit.usd-dev p.pkgs.git ];
          PXR_PLUGINPATH_NAME = "${p.pluginSet}";
          shellHook = "unset PYTHONPATH";
        };
      });
    };
}
