import os
import rclpy
import rclpy.node
import subprocess
import ament_index_python

def find_unity_version(project_dir: str):
    # Read the version of the Unity project from ""./ProjectSettings/ProjectVersion.txt".
    with open(os.path.join(project_dir, "ProjectSettings/ProjectVersion.txt")) as f:
        content = f.read()
        i = "".join(content).find("m_EditorVersion: ")
        if i == -1:
            raise RuntimeError("Failed to parse Unity project version.")
        version = content[i + len("m_EditorVersion: ") :].split("\n")[0]
        if version == "":
            raise RuntimeError("Failed to parse Unity project version.")
        
    return version

class UnitySim(rclpy.node.Node):
    def __init__(self):
        super().__init__('unity_sim')
        self.declare_parameter('scene', 'URC')

        # Find paths.
        with open(ament_index_python.packages.get_package_share_directory('unity_sim') + "/src-root") as f:
            project_dir = f.read()
        # (Either Distrobox host home or just $HOME without Distrobox.)
        running_in_distrobox = "DISTROBOX_HOST_HOME" in os.environ
        home = os.environ.get("DISTROBOX_HOST_HOME") if running_in_distrobox else os.environ.get("HOME")

        # Find Unity installation in ~/Unity/Hub/Editor/<version>.
        version = find_unity_version(project_dir)
        unity_dir = os.path.join(home, "Unity/Hub/Editor", version)
        if not os.path.isdir(unity_dir):
            raise RuntimeError(
                f"Failed to find Unity {version} at {unity_dir}.\nPlease install it on the host using Unity Hub.\nSee: https://unity.com/releases/editor/archive"
            )

        # Find the scene to run.
        scene = self.get_parameter('scene').get_parameter_value().string_value
        scene_path = os.path.normpath(f"{project_dir}/Assets/Simulation/Scenes/{scene}.unity")

        # Prepare the command.
        cmd = [os.path.join(unity_dir, "Editor/Unity"), "-openfile", scene_path]
        if running_in_distrobox:
            cmd = ["distrobox-host-exec"] + cmd
        
        # Run Unity.
        self.get_logger().info(f"Running Unity with command: {' '.join(cmd)}")
        subprocess.run(cmd)

# Simulation supervisor node.
def simulation(args=None):
    rclpy.init(args=args)

    UnitySim()

    rclpy.shutdown()

# Print the version of Unity.
def version(args=None):
    with open(ament_index_python.packages.get_package_share_directory('unity_sim') + "/src-root") as f:
        project_dir = f.read()
    version = find_unity_version(project_dir)
    print(f"Unity {version}")