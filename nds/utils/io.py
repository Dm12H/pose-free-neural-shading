import numpy as np
from pathlib import Path

import torch
import trimesh

from nds.core import Mesh, View
from nds.utils.idr import decompose

def read_mesh(path, device='cpu'):
    mesh_ = trimesh.load_mesh(str(path), process=False)

    vertices = np.array(mesh_.vertices, dtype=np.float32)
    indices = None
    if hasattr(mesh_, 'faces'):
        indices = np.array(mesh_.faces, dtype=np.int32)

    return Mesh(vertices, indices, device)

def write_mesh(path, mesh):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    vertices = mesh.vertices.numpy()
    indices = mesh.indices.numpy() if mesh.indices is not None else None
    mesh_ = trimesh.Trimesh(vertices=vertices, faces=indices, process=False)
    mesh_.export(path)

def read_views(directory, scale, device, approx=False):
    assert isinstance(directory, Path), "view directory must be a path"

    image_paths = sorted([path for path in directory.iterdir() if (path.is_file() and path.suffix == '.png')])
    if approx:
        init_poses = np.load(directory.parent / "cameras_linear_init.npz")
    views = []
    for image_path in image_paths:
        view = View.load(image_path, device)
        if approx:
            view_idx = int(image_path.stem[3:])
            _, R_init, t_init = decompose(init_poses[f"world_mat_{view_idx}"][:3, :])
            view.camera.R = torch.tensor(R_init, dtype=torch.float32).to(device)
            view.camera.t = torch.tensor(t_init, dtype=torch.float32).to(device)
        if scale > 1:
            view.scale(scale)
        views.append(view)
    print("Found {:d} views".format(len(views)))

    if scale > 1:
        print("Scaled views to 1/{:d}th size".format(scale))

    return views

