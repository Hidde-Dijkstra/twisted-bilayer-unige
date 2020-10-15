# -*- coding: utf-8 -*-
# ---
# jupyter:
#   jupytext:
#     formats: md:myst,py:light,ipynb
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.6.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# # Moiré functions

# ## Dependencies

import numpy as np
import plotly.graph_objects as go
import drawSvg as draw
from numpy.linalg import matrix_power as mat_pow


# ## Utility functions

# +
def rot_mat(θ):
    return np.array([[np.cos(θ), -np.sin(θ)], [np.sin(θ), np.cos(θ)]])

def arrow(start, end, stroke_width=0.1, stroke='black', **kwargs):
    start, end = np.array(start), np.array(end)
    Δx = 3
    my_arrow = draw.Marker(-1+Δx/4, -0.5, Δx/4, 0.5, scale=4, orient='auto')
    my_arrow.append(draw.Lines(-1+Δx/4, -0.5, -1+Δx/4, 0.5, Δx/4, 0, close=True, fill=stroke))
    p = draw.Path(stroke=stroke, stroke_width=stroke_width, fill='none',
              marker_end=my_arrow, **kwargs)
    t = 1 - stroke_width*Δx/np.linalg.norm(end-start)
    return p.M(*start).L(*(t*(end-start)+start))


# -

# ## Lattice drawing class

# +
class Index:
 

    def __init__(self, i, j):
        self.i = i
        self.j = j
        
    def __mul__(self, other):
        return self.i * other[0] + self.j * other[1]
    
    def __rmul__(self, other):
        return self * other
        
        
class Lattice:
    
    
    def __init__(self, a_1, a_2, W, H, θ=0):
        self.a = [np.array(a_1), np.array(a_2)]
        self.W = W
        self.H = H
        self.unit_cell = []
        self.grid = []
        self.θ = -θ
        
    def add_atom(self, atom):        
        N_1, N_2 = [1+min(int(self.W/np.abs(a[0]+0.00001)), int(self.H/np.abs(a[1]+0.00001))) for a in [rot_mat(self.θ)@a for a in self.a]]
        self.unit_cell.append(atom)
        if atom.atom_radius == None:
            atom.atom_radius = min([np.linalg.norm(a) for a in self.a]) / min(N_1, N_2) / 5 
        self.grid.append([Index(i, j) for i in range(-N_1, N_1+1) for j in range(-N_2, N_2+1) if self.in_lattice(i, j, atom)])
        
    def in_lattice(self, i, j, atom):
        origin = np.abs(rot_mat(self.θ) @ (atom.position+Index(i, j)*self.a))
        return np.all(origin-atom.atom_radius < [self.W/2, self.H/2])
        
    def NN(self, atom_1, atom_2, bond_list, **kwargs):
        #atom_1.bond_style.append(kwargs)
        for bond in bond_list:
            atom_1.bonds.append(atom_2.position+Index(*bond)*self.a)
            if atom_1 != atom_2:
                #atom_2.bond_style.append(kwargs)
                atom_2.bonds.append(-atom_1.bonds[-1])
    
    def draw_lattice(self, origin=(0, 0)):
        group = draw.Group()
        for i, atom in enumerate(self.unit_cell):
            for grid_point in self.grid[i]:
                group.append(atom.draw_bonds(grid_point*self.a, self.θ), z=0)                
                group.append(atom.draw_atom(grid_point*self.a, self.θ), z=1)
        return group
               
    def draw_lattice_vectors(self, vec_symbols=['a₁', 'a₂'], origin=(0, 0), centralize=True, stroke_width=0.1, color='black',
                             **kwargs):
        rot = rot_mat(self.θ)
        group = draw.Group()
        if centralize:
            origin += sum(self.a) / 2
        group.append(arrow(rot@origin, rot@(origin+self.a[0]), stroke_width=stroke_width, stroke=color, **kwargs))
        group.append(arrow(rot@origin, rot@(origin+self.a[1]), stroke_width=stroke_width, stroke=color, **kwargs))
        group.append(draw.Text(vec_symbols[0], stroke_width*10, *(rot@(origin+self.a[0])), fill=color))
        group.append(draw.Text(vec_symbols[1], stroke_width*10, *(rot@(origin+self.a[1])), fill=color))
        return group
    
    def draw_unit_cell(self, origin=(0, 0), **kwargs):
        rot = rot_mat(self.θ)
        group = draw.Group()
        for i in range(2):
            N = int(np.sqrt(self.H**2+self.W**2)/np.linalg.norm(self.a[1-i])) + 1
            for j in range(-N, N+1):
                vector = np.sqrt(self.H**2+self.W**2) * self.a[i]/np.linalg.norm(self.a[i])
                group.append(draw.Line(*(rot@(origin-vector+j*self.a[1-i])), *(rot@(origin+vector+j*self.a[1-i])), **kwargs))
        return group
    


class LatticeAtom:
    
    
    def __init__(self, position_in_unit_cell, name=None, atom_color='blue', atom_radius=None):       
        self.position = np.array(position_in_unit_cell)
        self.name = name
        self.atom_color = atom_color
        self.atom_radius = atom_radius
        self.bonds = []
        self.bond_style = []
    
    def draw_bonds(self, displacement, θ, **kwargs):
        group = draw.Group()
        origin = rot_mat(θ) @ (displacement + self.position)
        for bond in self.bonds:
            group.append(draw.Line(*origin, *(origin+bond), stroke='black', stroke_width=0.01, **kwargs))
        return group
    
    def draw_atom(self, displacement, θ, **kwargs):
        group = draw.Group()
        origin = rot_mat(θ) @ (displacement + self.position)
        gradient = draw.RadialGradient(*origin, self.atom_radius)
        gradient.addStop(0, 'white', 1)
        gradient.addStop(1, self.atom_color, 1)
        group.append(draw.Circle(*origin, self.atom_radius, stroke='black', stroke_width=0.01, fill=gradient, **kwargs))
        if self.name != None:
            group.append(draw.Text(self.name, self.atom_radius, *origin, text_anchor='middle', alignment_baseline="central"))
        return group


# -

# ## Drawing orbitals

class Orbital:  
    
    
    def lobe(self, color, rotate=0, translate=(0, 0), stroke="black", **kwargs):
        gradient = draw.RadialGradient(0, 1, 0.5)
        gradient.addStop(0, 'white', 0.7)
        gradient.addStop(np.sqrt(3), color, 0.7)
        transform = "translate(" + " ".join([str(i) for i in translate]) + ")\nrotate(" + str(rotate) + " 0 0)"
        my_path = "M 0,0 C " + str(-np.sqrt(3)) + ",-2 " + str(np.sqrt(3)) +",-2 0,0 z"
        return draw.Path(d=my_path, stroke=stroke, stroke_width=0.01, fill=gradient, transform=transform, **kwargs)
    
    def circle(self, color, ellipse=False, rotate=0, translate=(0, 0), stroke="black", **kwargs):
        gradient = draw.RadialGradient(0, 0, 0.5)
        gradient.addStop(0, 'white', 0.7)
        gradient.addStop(np.sqrt(3), color, 0.7)
        transform = "rotate(" + str(rotate) + " 0 0)\ntranslate(" + " ".join([str(i) for i in translate]) + ")"
        if ellipse:
            clip = draw.ClipPath()
            clip.append(draw.Ellipse(0, 0, 0.5, 0.125, transform=transform))
            return draw.Ellipse(0, 0, 1, 0.25, stroke=stroke, stroke_width=0.01, fill=gradient, transform=transform, **kwargs) 
        else:
            return draw.Circle(0, 0, 0.5, stroke=stroke, stroke_width=0.01, fill=gradient, transform=transform, **kwargs)
    
    def d_xy(self, translate=(0, 0), rotate=0, neg_color="dodgerblue", pos_color="red",
             **kwargs):
        group = draw.Group(**kwargs)
        group.append(self.lobe(neg_color, rotate=85+rotate, translate=translate))
        group.append(self.lobe(pos_color, rotate=95+rotate, translate=translate))
        group.append(self.lobe(pos_color, rotate=275+rotate, translate=translate))
        group.append(self.lobe(neg_color, rotate=265+rotate, translate=translate))
        return group
    
    def d_z2(self, translate=(0, 0), rotate=0, neg_color="dodgerblue", pos_color="red",
             **kwargs):
        group = draw.Group(**kwargs)
        group.append(self.lobe(neg_color, rotate=180+rotate, translate=translate))
        group.append(self.circle(pos_color, ellipse=True, rotate=rotate, translate=translate))
        group.append(self.lobe(neg_color, rotate=rotate, translate=translate))
        return group
    
    def d_x2y2(self, translate=(0, 0), rotate=0, neg_color="dodgerblue", pos_color="red",
               **kwargs):
        group = draw.Group(**kwargs)
        group.append(self.lobe(neg_color, rotate=180+rotate, translate=translate))
        group.append(self.lobe(neg_color, rotate=rotate, translate=translate))
        group.append(self.lobe(pos_color, rotate=90+rotate, translate=translate))
        group.append(self.lobe(pos_color, rotate=270+rotate, translate=translate))
        return group


# ## Band structure calculations

class BandStructure:
    
    
    def __init__(self, H):
        self.H = H
          
    def plot_band_structure(self, σ_list=[0], E_ref=None):
        colors = ['blue', 'red', 'green']
        N = len(self.H((0, 0), 1))
        energies = np.zeros((len(self.k_path), N, len(σ_list)))
        for i in range(len(self.k_path)):
            for j in range(len(σ_list)):
                energies[i, :, j] = np.linalg.eigvalsh(self.H(self.k_path[i], σ_list[j]))
        fig = go.Figure()        
        for j in range(len(σ_list)):
            style_dict = {
                'legendgroup': 'σ='+str(σ_list[j]),
                'mode': 'lines',
                'line': {'color': colors[j]},
                'name': 'σ='+str(σ_list[j])
            }
            fig.add_trace(go.Scatter(y=energies[:, 0, j], **style_dict))
            for i in range(1, N):
                fig.add_trace(go.Scatter(y=energies[:, i, j], showlegend=False, **style_dict))
        fig.update_xaxes(ticktext=self.k_tags, tickvals=[sum(self.spacing[:i]) for i in range(len(self.spacing)+1)])
        if E_ref != None:
            fig.update_yaxes(tickvals=E_ref)
        fig.update_layout(xaxis_title=r"$k$", yaxis_title= 'Energy (eV)')
        return fig
    
    def set_k_path(self, k_list, k_tags, N_points):
        self.k_tags = k_tags
        k_norms = [np.linalg.norm(k_list[i+1]-k_list[i]) for i in range(len(k_list)-1)]
        self.spacing = [int(N_points*k_norms[i]/sum(k_norms)) for i in range(len(k_norms))]
        self.k_path = []
        for i in range(len(self.spacing)):
            self.k_path += [k_list[i] + (k_list[i+1]-k_list[i])*j/self.spacing[i] for j in range(self.spacing[i])]
        self.k_path += [k_list[-1]]


# ## Moiré supercell class

# +
class LatVec:
    # We identify each atom as the two integers i and j which connect it to the origin. 
    # Using a pythonic object we can define how two of these vectors interact.
    a_1 = np.array([1, 0])
    a_2 = np.array([1/2, np.sqrt(3)/2])
    b_1 = 2*np.pi * np.array([1, -1/np.sqrt(3)])
    b_2 = 2*np.pi * np.array([0, 2/np.sqrt(3)])
    
    
    def __init__(self, i, j, reciprocal=False, scale=1):
        self.i = i
        self.j = j
        self.scale = scale
        self.reciprocal = reciprocal
        self.vec = self.vectorize()
        
    def __add__(self, other):
        return LatVec(self.i+other.i, self.j+other.j)
    
    def __sub__(self, other):
        return LatVec(self.i-other.i, self.j-other.j)
    
    def __eq__(self, other):
        return (self.i==other.i) & (self.j==other.j)
    
    def __and__(self, other):
        # A simple way to get all hopping vectors from two unit vectors.
        return [self, other.neg(), self.neg()+other.neg(), self.neg(), other, self+other]
    
    def __mul__(self, other):
        if type(other) == LatVec:
            return np.dot(self.vec, other.vec)
        else:
            return np.dot(self.vec, other)
        
    def __rmul__(self, other):
        return self * other
    
    def neg(self):
        return LatVec(-self.i, -self.j)
    
    def rot(self, θ):
         return np.array([[np.cos(θ), -np.sin(θ)], [np.sin(θ), np.cos(θ)]]) @ self.vec
    
    def vectorize(self):
        if self.reciprocal:
            return self.scale*(self.i*self.b_1 + self.j*self.b_2)
        else:
            return self.scale*(self.i*self.a_1 + self.j*self.a_2)
        
class Supercell:
    hop_list = LatVec(1, 0) & LatVec(0, -1)
    
    def __init__(self, m, n):
        self.v_1 = LatVec(m, n)    
        self.v_2 = LatVec(n+m, -m)
        self.w_1 = LatVec(m, n+m, True, 1/(m**2+m*n+n**2))
        self.w_2 = LatVec(n, -m, True, 1/(m**2+m*n+n**2))
        r = max(m, n)
        self.grid = [LatVec(i, j) for i in range(0, 3*r) for j in range(-r, r+1) if self.in_supercell(i, j)]
        self.N_atoms = len(self.grid)
        self.Δθ = np.arctan((n-m)/(n+m)/np.sqrt(3))
        self.construct_NN_array()
         
    def in_supercell(self, i, j, tol=10**-5):
        M = np.linalg.inv(np.array([self.v_1.vec, self.v_2.vec]).T)
        λ, μ = M @ LatVec(i, j).vec
        in_parellogram = (tol < λ < 1-tol) and (tol < μ < 1-tol) 
        return in_parellogram or (i, j) == (0, 0)
    
    def construct_NN_array(self):
        self.NN_array = []
        for i in range(self.N_atoms):
            self.NN_array.append([self.find_NN(i, h_vec) for h_vec in self.hop_list])
            
    def find_NN(self, i, h_vec):
        for lat_vec in (self.v_1 & self.v_2) + [LatVec(0, 0)]:
            if self.grid[i]+h_vec-lat_vec in self.grid:
                return {'NN': self.grid.index(self.grid[i]+h_vec-lat_vec),
                        'LatVec': lat_vec
                       }
        raise Exception('No NN found for '+str(i)+' '+str(h_vec))
                
    def interlayer_hopping_array(self, supercell, tol=10**-5):
        if self.N_atoms != supercell.N_atoms:
            raise Exception('Supercells have a different number of atoms')
        if np.abs(self.Δθ + supercell.Δθ) > tol:
            raise Exception('Unequal twist angles')
        z_hopping = np.zeros((self.N_atoms, self.N_atoms, 2))
        for i in range(self.N_atoms):
            vec_i = supercell.grid[i].rot(-supercell.Δθ)    
            for j in range(self.N_atoms):
                min_ΔR = 10**6
                for lat_vec in (self.v_1 & self.v_2) + [LatVec(0, 0)]:
                    vec_j_trial = (self.grid[j]+lat_vec).rot(-self.Δθ)
                    if np.linalg.norm(vec_i-vec_j_trial) < min_ΔR:
                        min_ΔR = np.linalg.norm(vec_i-vec_j_trial)
                        vec_j = vec_j_trial
                z_hopping[i, j] = vec_i - vec_j
        return z_hopping
                        
    def lattice(self, W, H, rotate=True, atom_color='blue', atom_radius=0.2):
        supercell = Lattice(self.v_1.vec, self.v_2.vec, W, H, θ=self.Δθ*rotate)
        for atom in self.grid:
            supercell.add_atom(LatticeAtom(atom.vec, atom_color=atom_color, atom_radius=atom_radius))
        return supercell
    
    def reduce_k_point(self, k):
        α, β = np.linalg.inv([[self.w_1*self.w_1, self.w_1*self.w_2], [self.w_1*self.w_2, self.w_2*self.w_2]]) @ np.array([np.dot(k, self.w_1.vec), np.dot(k, self.w_2.vec)]).T
        return np.modf(α)[0]*self.w_1.vec + np.modf(β)[0]*self.w_2.vec


# -

# ## WSe$_2$ specific calculations

class WSe2:
    var_dic = {
        "t_1": 0.034, 
        "t_2": 0.263, 
        "t_3": -0.207, 
        "t_12": 0.329, 
        "t_13": 0.486, 
        "t_23": 0.457, 
        "ε_1": 2.179, 
        "ε_3": 0.942, 
        "λ_SOC": 0.228
    }
    t_1, t_2, t_3, t_12, t_13, t_23, ε_1, ε_3, λ_SOC = var_dic.values()
    E_mat = np.array([[t_1, t_12, t_13],
                      [-t_12, t_2, t_23],
                      [t_13, -t_23, t_3]])
    E_levels = np.diag([ε_1, ε_1, ε_3])
    E_0 = E_levels[0, 0] - 3/2*(E_mat[1, 1]+E_mat[0, 0]) - 3*np.sqrt(3)*E_mat[0, 1]
    E_1 = E_levels[2, 2] - 3*E_mat[2, 2]
    λ_SOC = 0.228
    d = 2.4
    λ = 0.3
    
    def __init__(self, m, n, R_max=1):
        self.layer_1 = Supercell(m, n)
        self.layer_2 = Supercell(n, m)
        self.z_hopping = self.layer_1.interlayer_hopping_array(self.layer_2)
        R = np.array([[-1/2, -np.sqrt(3)/2, 0], [np.sqrt(3)/2, -1/2, 0], [0, 0, 1]])
        C_2 = np.diag([1, -1, 1])
        self.E_list = [mat_pow(R, i)@mat_pow(C_2, i)@self.E_mat@(mat_pow(R, i)@mat_pow(C_2, i)).T for i in range(6)]
        z_hopping = self.layer_1.interlayer_hopping_array(self.layer_2)
        self.z_hop = []
        for i in range(self.layer_1.N_atoms):
            self.z_hop += [[(j, z_hopping[i, j]) for j in range(self.layer_2.N_atoms) if np.linalg.norm(z_hopping[i, j])<R_max]]
            
    def H_mono(self, k, σ):
        k_x, k_y = k[0]/2, k[1]*np.sqrt(3)/2
        cos2x, cosx, cosy = np.cos(2*k_x), np.cos(k_x), np.cos(k_y)
        sin2x, sinx, siny = np.sin(2*k_x), np.sin(k_x), np.sin(k_y)
        h_1 = 2*self.t_1*cos2x + (self.t_1+3*self.t_2)*cosx*cosy
        h_2 = 2*self.t_2*cos2x + (self.t_2+3*self.t_1)*cosx*cosy
        h_3 = 2*self.t_3*cos2x + 4*self.t_3*cosx*cosy
        h_12 = np.sqrt(3)*(self.t_1-self.t_2)*sinx*siny + 2j*self.t_12*(sin2x-2*sinx*cosy)
        h_13 = 2*self.t_13*(cos2x-cosx*cosy) + 2j*np.sqrt(3)*self.t_23*cosx*siny
        h_23 = -2*np.sqrt(3)*self.t_13*sinx*siny + 2j*self.t_23*(sin2x+sinx*cosy)
        return np.array([
            [self.ε_1+h_1, 1j*self.λ_SOC*σ+h_12, h_13],
            [-1j*self.λ_SOC*σ+np.conj(h_12), self.ε_1+h_2, h_23],
            [np.conj(h_13), np.conj(h_23), self.ε_3+h_3]
        ])
    
    def H_WSe2_mono(self, k, σ, layer, rotate=False):
        if rotate:
            k = np.array([[np.cos(layer.Δθ), -np.sin(layer.Δθ)], [np.sin(layer.Δθ), np.cos(layer.Δθ)]]) @ k
        H = np.zeros((3*layer.N_atoms, 3*layer.N_atoms), dtype=complex)
        for i in range(layer.N_atoms):
            H[3*i:3*(i+1), 3*i:3*(i+1)] = self.E_levels + self.λ_SOC*np.array([[0, 1j*σ, 0], [-1j*σ, 0, 0], [0, 0, 0]])
            for j in range(6):
                m = layer.NN_array[i][j]['NN']
                H[3*i:3*(i+1), 3*m:3*(m+1)] = self.E_list[j] * np.exp(1j*np.dot(layer.NN_array[i][j]['LatVec'].vec, k))
        my_H = (sum([self.E_list[j] * np.exp(1j*np.dot(layer.hop_list[j].vec, k)) for j in range(6)]) 
                    + self.E_levels + self.λ_SOC*np.array([[0, 1j*σ, 0], [-1j*σ, 0, 0], [0, 0, 0]]))
        
        return my_H
            
    def H_WSe2_bilayer(self, k, σ, t_0):
        H = np.zeros((6*self.layer_1.N_atoms, 6*self.layer_1.N_atoms), dtype=complex)
        H[0:3*self.layer_1.N_atoms, 0:3*self.layer_1.N_atoms] = self.H_WSe2_mono(k, σ, self.layer_1, rotate=True)
        H[3*self.layer_1.N_atoms:, 3*self.layer_1.N_atoms:] = self.H_WSe2_mono(k, σ, self.layer_2, rotate=True)
        for i in range(self.layer_1.N_atoms):
            for j, hop_vec in self.z_hop[i]:
                t = t_0 * np.exp(-(np.sqrt(np.dot(hop_vec, hop_vec)+self.d**2)-self.d)/self.λ)
                H[3*i+2+3*self.layer_1.N_atoms, 3*j+2] = t * np.exp(1j*np.dot(k, hop_vec))
                H[3*j+2, 3*i+2+3*self.layer_1.N_atoms] = t * np.exp(-1j*np.dot(k, hop_vec))
        return H
        


