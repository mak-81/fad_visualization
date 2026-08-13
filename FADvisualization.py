import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.gridspec import GridSpec
import numpy as np
import streamlit as st

# Page setup
st.set_page_config(
    page_title="Pipe Crack Assessment", page_icon="🎯", layout="wide"
)
st.title("Through-Wall Crack Assessment in Pressurized Pipe")
st.markdown("### FAD analysis using the **Folias factor**.")
st.markdown(r"$$M_T = \sqrt{1 + 1.255 \left(\frac{c^2}{R t}\right) - 0.0135 \left(\frac{c^4}{(R t)^2}\right)}$$")
st.markdown(r"$$\sigma_{ref} = M_T \left( \frac{P \cdot R}{t} \right) ; K_I= M_T \left( \frac{P \cdot R}{t} \right) \sqrt{\pi c} ; L_r=\frac{\sigma_{ref}}{\sigma_y}; K_r=\frac{K_{I}}{K_{mat}}  $$")


# Constant pipeline dimensions
R = 100  # pipeline radius (mm)
t = 10  # pipeline thickness (mm)


# Math functions
def FAL(Lr, YS, UTS):
    """Failure Assessment Line (FAL) calculation"""
    y = np.zeros_like(Lr)
    mask = Lr <= (YS + UTS) / (2 * YS)
    y[mask] = (1 - 0.14 * Lr[mask] ** 2) * (
        0.3 + 0.7 * np.exp(-0.65 * Lr[mask] ** 6)
    )
    return y


def sigma_using_Folias_factor(c, t, R, P):
    """Stress calculation using Folias factor"""
    return (P * R / t) * (
        1 + 1.255 * c**2 / (t * R) - 0.0135 * c**4 / ((t * R) ** 2)
    ) ** (1 / 2)


# --- Sidebar Inputs ---
st.sidebar.header("Assessment Parameters")

YS = st.sidebar.slider("Yield Stress $\sigma_y$ (MPa)", 300, 1000, 500)
P = st.sidebar.slider("Pressure $P$ (MPa)", 1, 100, 10)
c = st.sidebar.slider("Half Crack Length $c$ (mm)", 0.0, 50.0, 10.0, step=0.5)
Kmat = st.sidebar.slider("Fracture Toughness $K_{mat}$ (MPa·m$^{1/2}$)", 10, 500, 100)

UTS = YS * 1.2  # Ultimate Tensile Strength estimate

# --- Calculations ---
lr_axis = np.arange(0, 1.21, 0.001)
fal_curve = FAL(lr_axis, YS, UTS)

sigma = sigma_using_Folias_factor(c, t, R, P)
Lr_point = sigma / YS
Kr_point = sigma *  ((np.pi *c / 1000) ** (1 / 2)) / Kmat
FAL_at_Lr = FAL(np.array([Lr_point]), YS, UTS)[0]

is_safe = (Kr_point <= FAL_at_Lr and Lr_point<=1.1)

# --- UI Layout ---
col1, col2 = st.columns([3, 1])

with col1:
    # Plot generation
    
    fig = plt.figure(figsize=(8, 5))
    fig.suptitle(f"Through-wall crack in pipe (t={t} mm, R={R} mm)")
    gs = GridSpec(2, 1,  height_ratios=[1, 2])
    ax2 = fig.add_subplot(gs[0])
    ax = fig.add_subplot(gs[1])
    
    
        
    ax.plot(lr_axis, fal_curve, label="FAL", color="blue", linewidth=2)

    # Plot assessment point & assessment line
    ax.plot([0, Lr_point], [0, Kr_point], color="red", linestyle="--", alpha=0.7)
    ax.plot(
        Lr_point,
        Kr_point,
        color="green" if is_safe else "red",
        marker="X",
        markersize=10,
        label="Assessment Point",
    )

    ax.set_xlabel(r"$L_r$", fontsize=14)
    ax.set_ylabel(r"$K_r$", fontsize=14)
    ax.set_xlim([0, 1.2])
    ax.set_ylim([0, 1.1])
    ax.grid(True, linestyle="-", alpha=0.7)
    ax.legend()

   
# Make a drawing for the pipe with through wall flaw
    rect1 = Rectangle((0, 0), 1, .05, facecolor='grey', edgecolor='black')
    rect2 = Rectangle((0, .95), 1, .05, facecolor='grey', edgecolor='black')
    rect3 = Rectangle((.5-c/400, .95), c/200, .05, facecolor='white', edgecolor='black')
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.annotate('', xy=(0, .5), xycoords='axes fraction', xytext=(1, .5),arrowprops=dict(arrowstyle="-", color='k',ls="-."))
    ax2.annotate('', xy=(.5-c/400, .9), xycoords='axes fraction', xytext=(.5+c/400, .9),arrowprops=dict(arrowstyle="<->", color='k',ls="-"))
    ax2.text(.45, .77, 'L=2c='+f"{2*c:.0f} mm",color="black", fontsize=12)
    ax2.text(.45, .35, "P="+ f"{P:.0f} MPa",color="black", fontsize=10+int(P/5))
    ax2.text(.02, .1, "$\sigma_{y}=$"+f"{YS:.0f} MPa",color="black", fontsize=11)
    ax2.text(.00, .07, "↙", fontsize=12)
    ax2.text(.20, .07, "↙", fontsize=12)    
    ax2.text(.22, .1, "$K_{mat}=$"+f"{Kmat:.0f}"+"MPa·m$^{1/2}$",color="black", fontsize=11)
    ax2.add_patch(rect1)
    ax2.add_patch(rect2)
    ax2.add_patch(rect3)



    st.pyplot(fig)

with col2:
    st.subheader("Assessment Result")
    if is_safe:
        st.success("### SAFE")
    else:
        if (Kr_point/Lr_point)>(FAL(np.array([.4]), YS, UTS)[0]/.4):
            st.error("### FAIL, brittle fracture")
        else:
            if (Kr_point/Lr_point)<(FAL(np.array([1.09]), YS, UTS)[0]/1.09):
                st.error("### FAIL, plastic collapse")
            else:
                st.error("### FAIL, elastoplastic fracture")
    st.divider()
    st.metric("$\sigma_{hoop}$", f"{(100*P*R/t)/YS:.1f} %$\sigma_y$")
    st.metric("$\sigma_{ref}$", f"{sigma:.0f} MPa")
    st.metric("$L_r$", f"{Lr_point:.3f}")
    st.metric("$K_r$", f"{Kr_point:.3f}")
