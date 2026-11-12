#!/usr/bin/env python3
"""Generate the four VeriRoute Stage 3 visuals in the CYBER_BLENDED palette."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

HERE = Path(__file__).resolve().parent
if HERE.name == 'scripts':
    PROJECT = HERE.parent
    OUT = PROJECT.parent
    ASSETS = PROJECT / 'assets'
else:
    OUT = HERE
    PROJECT = HERE / 'veriroute-stage3-confidence-routing'
    ASSETS = PROJECT / 'assets'
ASSETS.mkdir(parents=True, exist_ok=True)
PINK = '#FF2A85'
PURPLE = '#8570FF'
GREEN = '#10B981'
AMBER = '#F59E0B'
BG = '#0B0813'
CARD = '#161224'
WHITE = '#F3F1F8'
MUTED = '#B5AEC8'
plt.rcParams.update({
    'font.family':'DejaVu Sans', 'text.color':WHITE, 'axes.labelcolor':WHITE,
    'xtick.color':WHITE, 'ytick.color':MUTED, 'figure.facecolor':BG,
    'axes.facecolor':CARD, 'savefig.facecolor':BG, 'axes.titleweight':'bold',
    'font.size':11,
})

def style_ax(ax):
    ax.set_facecolor(CARD)
    ax.grid(axis='y', color='#5B526F', alpha=.25, linewidth=.8)
    ax.set_axisbelow(True)
    for s in ax.spines.values(): s.set_color('#393047')
    ax.tick_params(colors=MUTED, labelsize=10)

def save(fig, name):
    fig.savefig(OUT/name, dpi=300, facecolor=BG, bbox_inches='tight', pad_inches=.18)
    fig.savefig(ASSETS/name, dpi=300, facecolor=BG, bbox_inches='tight', pad_inches=.18)
    plt.close(fig)

def heading(fig, title, subtitle=None):
    fig.text(.5,.965,title,ha='center',va='top',color=PINK,fontsize=19,fontweight='bold')
    if subtitle: fig.text(.5,.925,subtitle,ha='center',va='top',color=MUTED,fontsize=10.5)

def chart1():
    fig=plt.figure(figsize=(14,8),facecolor=BG)
    heading(fig,'SEMANTIC GENERALIZATION HELD STRONG // ZERO OVERFITTING',
        'Unseen conversational paraphrases (zero keyword overlap) outperformed the semantic baseline across every metric')
    ax=fig.add_axes([.09,.23,.82,.61]); style_ax(ax)
    cats=['Top-1 Policy\nAccuracy','Tier 1 Auto-Resolve\nCoverage (≥ 0.45)','Tier 1 Auto-Send\nPrecision']
    baseline=[74.4,40.0,86.0]; holdout=[80.0,63.3,92.1]
    x=np.arange(3); w=.34
    b1=ax.bar(x-w/2,baseline,w,color=PURPLE,label='125-Query Semantic Baseline (Stage 2)',zorder=3)
    b2=ax.bar(x+w/2,holdout,w,color=GREEN,label='60 Unseen Semantic Holdout (HOLD-001–060)',zorder=3)
    ax.set_ylim(0,112); ax.set_ylabel('Metric (%)',fontsize=11); ax.set_xticks(x,cats,fontsize=10)
    ax.set_title('SEMANTIC HOLDOUT PERFORMANCE',color=WHITE,fontsize=13,pad=14)
    ax.legend(loc='upper left',frameon=True,facecolor=BG,edgecolor='#393047',labelcolor=WHITE,fontsize=9)
    for bars in (b1,b2):
        for bar in bars:
            ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+2,f'{bar.get_height():.1f}%',ha='center',va='bottom',fontsize=10,fontweight='bold',color=WHITE)
    for i,(val,delta) in enumerate(zip(holdout,['+5.6% pts','+23.3% pts','+6.1% pts'])):
        ax.text(x[i]+w/2,val-10,delta,ha='center',va='center',fontsize=8.5,fontweight='bold',color=BG,
                bbox=dict(boxstyle='round,pad=.35',fc=AMBER,ec=AMBER,lw=0))
    fig.text(.5,.10,'HOLDOUT GENERALIZATION  /  ALL THREE METRICS IMPROVED',ha='center',color=AMBER,fontsize=10,fontweight='bold')
    save(fig,'chart1_semantic_generalization.png')

def chart2():
    fig=plt.figure(figsize=(14,8),facecolor=BG)
    heading(fig,'THE SIBLING-POLICY LEXICAL DROP // TOP-1 RETRIEVAL ACCURACY',
      'Harder lexical holdout queries (HOLD-061–120) exposed sibling-policy score compression')
    ax=fig.add_axes([.09,.19,.82,.66]); style_ax(ax)
    x=np.array([0,1]); semantic=[74.4,80.0]; lexical=[97.6,56.7]
    ax.plot(x,semantic,color=GREEN,marker='o',markersize=10,linewidth=3,label='Semantic Intent Queries (+5.6% pts)',zorder=4)
    ax.plot(x,lexical,color=PINK,marker='o',markersize=10,linewidth=3,label='Lexical Keyword Queries (-40.9% pts)',zorder=4)
    ax.set_xlim(-.25,1.25); ax.set_ylim(20,110); ax.set_ylabel('Top-1 Policy Retrieval Accuracy (%)')
    ax.set_xticks(x,['250-Ticket Baseline\n(Curated Corpus)','150-Query Holdout\n(Unseen Stress Test)'])
    ax.set_title('RETRIEVAL ACCURACY BY QUERY TYPE',color=WHITE,fontsize=13,pad=12)
    ax.legend(loc='upper right',frameon=True,facecolor=BG,edgecolor='#393047',labelcolor=WHITE,fontsize=9)
    for px,py in zip(x,semantic): ax.annotate(f'{py:.1f}%',(px,py),xytext=(0,-20),textcoords='offset points',ha='center',color=GREEN,fontweight='bold',fontsize=10)
    for px,py in zip(x,lexical): ax.annotate(f'{py:.1f}%',(px,py),xytext=(0,10),textcoords='offset points',ha='center',color=PINK,fontweight='bold',fontsize=10)
    ax.plot([.79,.79],[97.6,56.7],ls='--',color=AMBER,lw=1.8)
    ax.plot([.75,.83],[97.6,97.6],ls='--',color=AMBER,lw=1.5); ax.plot([.75,.83],[56.7,56.7],ls='--',color=AMBER,lw=1.5)
    box='SIBLING-POLICY COLLISION (-40.9% pts)\n• Shared sub-clauses (e.g., RET-SEAS vs. RET-204)\n• Jina semantic scores compressed in the grey zone\n• 20% RRF weight too small for exact BM25 tie-breaking'
    ax.annotate(box,xy=(1,56.7),xytext=(.22,31),textcoords='data',ha='left',va='center',fontsize=8.4,color=WHITE,
      bbox=dict(boxstyle='round,pad=.7',fc=BG,ec=AMBER,lw=1.6),
      arrowprops=dict(arrowstyle='->',color=AMBER,lw=1.6,connectionstyle='arc3,rad=-.12'))
    save(fig,'chart2_sibling_lexical_drop.png')

def chart3():
    fig=plt.figure(figsize=(15,8.5),facecolor=BG)
    heading(fig,'CONFIDENCE GATING IN ACTION // THROTTLING VOLUME TO PROTECT TRUST')
    ax1=fig.add_axes([.055,.25,.43,.60]); style_ax(ax1)
    ax2=fig.add_axes([.56,.25,.39,.60]); style_ax(ax2)
    ax1.set_title('1. Router Automatically Throttled Tier 1',color=WHITE,fontsize=12,fontweight='bold',pad=14)
    labels=['250-Query\nBaseline','60 Hard Lexical\nHoldout Queries']
    series=[('Tier 1: Auto-Resolve (≥ 0.45)',[64.0,26.7],GREEN),('Tier 2: Agent Copilot (0.22–0.45)',[34.4,56.7],PURPLE),('Tier 3: Zero-LLM Abstain (< 0.22)',[1.6,16.7],AMBER)]
    bottoms=np.zeros(2)
    for label,vals,c in series:
        ax1.bar([0,1],vals,bottom=bottoms,color=c,width=.55,label=label,edgecolor=BG,linewidth=.6,zorder=3)
        for i,v in enumerate(vals):
            if v>=10: ax1.text(i,bottoms[i]+v/2,f'{v:.1f}%',ha='center',va='center',fontsize=9,color=BG,fontweight='bold')
        bottoms+=np.array(vals)
    ax1.set_ylim(0,112); ax1.set_xticks([0,1],labels,fontsize=9); ax1.set_ylabel('Query volume (%)')
    ax1.legend(loc='upper left',bbox_to_anchor=(0,-.16),frameon=False,labelcolor=WHITE,fontsize=7.6,ncol=1)
    ax1.annotate('Auto-Throttled\nby -37.3% pts\n(-61.3% vs Lexical)!',xy=(1,26.7),xytext=(.35,94),ha='center',va='center',fontsize=9,color=WHITE,
       bbox=dict(boxstyle='round,pad=.55',fc=BG,ec=AMBER,lw=1.5),arrowprops=dict(arrowstyle='->',color=AMBER,lw=1.6))
    ax2.set_title('2. Confidence Gate Protected Precision',color=WHITE,fontsize=12,fontweight='bold',pad=14)
    vals=[56.7,88.9,0.0]; colors=[PINK,GREEN,AMBER]
    bars=ax2.bar([0,1,2],vals,color=colors,width=.55,zorder=3)
    ax2.set_ylim(0,112); ax2.set_xlim(-.5,6.5); ax2.set_ylabel('Reported rate (%)', labelpad=6)
    ax2.set_xticks([0,1,2],['Hard Lexical\nTop-1 Accuracy','Overall Tier 1\nAuto-Send Precision','Hallucination\nLeak Rate'],fontsize=8.3)
    for i,(bar,v) in enumerate(zip(bars,vals)):
        if v: ax2.text(i,v+3,f'{v:.1f}%',ha='center',color=colors[i],fontsize=10,fontweight='bold')
        else: ax2.text(i,4,'0.0%\n(Zero Leaks)',ha='center',va='bottom',color=AMBER,fontsize=8.5,fontweight='bold')
    ax2.annotate('LIVE VERIFIER SAVE (HOLD-033)\n• Caught ungrounded 48-hr SLA\n  hallucination before dispatch\n• Forced live downgrade to\n  Tier 2 Human Hold Queue',xy=(1,88.9),xytext=(4.5,55),ha='center',va='center',fontsize=8.2,color=WHITE,
      bbox=dict(boxstyle='round,pad=.6',fc=BG,ec=AMBER,lw=1.5),arrowprops=dict(arrowstyle='->',color=AMBER,lw=1.5))
    fig.text(.5,.08,'TRUST-FIRST ROUTING  /  AUTOMATION VOLUME YIELDS WHEN CONFIDENCE FALLS',ha='center',color=AMBER,fontsize=10,fontweight='bold')
    save(fig,'chart3_confidence_gating.png')

def box(ax,xy,w,h,title,lines,border,headfill=None,fontsize=7.2, title_size=8.1):
    x,y=xy
    patch=FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.012,rounding_size=0.018',transform=ax.transAxes,
      fc=CARD,ec=border,lw=1.4)
    ax.add_patch(patch)
    pill=FancyBboxPatch((x+.015,y+h-.075),w-.03,.052,boxstyle='round,pad=.008,rounding_size=.012',transform=ax.transAxes,
      fc=headfill or border,ec='none',alpha=.95)
    ax.add_patch(pill)
    ax.text(x+w/2,y+h-.049,title,transform=ax.transAxes,ha='center',va='center',fontsize=title_size,color=BG,fontweight='bold')
    yy=y+h-.105
    step=min(.047, max(.026, (h-.13)/max(1,len(lines)-1)))
    for text,color in lines:
        ax.text(x+.025,yy,text,transform=ax.transAxes,ha='left',va='top',fontsize=fontsize,color=color,linespacing=1.15)
        yy-=step

def hero():
    fig=plt.figure(figsize=(16,9.7),facecolor=BG)
    fig.text(.045,.965,'VERIROUTE AI // STAGE 3 CIRCUIT-BREAKER ARCHITECTURE',color=PINK,fontsize=15,fontweight='bold',va='top')
    badge=FancyBboxPatch((.81,.945),.15,.037,boxstyle='round,pad=.01,rounding_size=.015',transform=fig.transFigure,fc=PINK,ec='none')
    fig.patches.append(badge); fig.text(.885,.963,'FAIL-CLOSED SPEC',transform=fig.transFigure,ha='center',va='center',fontsize=9,color=BG,fontweight='bold')
    fig.text(.5,.91,'Inside the Deterministic Tier 1 Verifier: Fault Injection, Temp Tuning & Fail-Closed Routing',ha='center',color=WHITE,fontsize=14,fontweight='bold')
    ax=fig.add_axes([.025,.075,.95,.80]); ax.set_axis_off(); ax.set_facecolor(BG)
    border=FancyBboxPatch((.005,.005),.99,.99,boxstyle='round,pad=.006,rounding_size=.025',transform=ax.transAxes,fc=BG,ec=PINK,lw=2)
    ax.add_patch(border)
    # columns, deliberately generous gaps to keep arrows/text independent
    box(ax,(.025,.60),.22,.30,'3-TIER CONFIDENCE GATE',[
      ('Contiguous Math Boundaries',WHITE),('• Tier 1: >= 0.4500',GREEN),('• Tier 2: 0.2200 - 0.4499',PURPLE),('• Tier 3: < 0.2200 (0 LLM)',AMBER),('• NaN/null -> Loud Fallback',PINK)],PURPLE,fontsize=7.3,title_size=8)
    ax.add_patch(FancyArrowPatch((.135,.58),(.135,.515),transform=ax.transAxes,arrowstyle='-|>',mutation_scale=14,color=PINK,lw=1.7))
    ax.text(.145,.55,'Score >= 0.45',transform=ax.transAxes,color=WHITE,fontsize=7.5,va='center')
    box(ax,(.025,.13),.22,.34,'TIER 1 CUSTOMER DRAFT',[
      ('Llama-3.3-70B Generator',WHITE),('TEMP = 0.1 (Natural)',AMBER),('Grounded in Top-1 Policy',MUTED),('Awaiting Audit Clearance',MUTED)],PINK,fontsize=8,title_size=8)
    # center verifier frame
    frame=FancyBboxPatch((.275,.105),.445,.79,boxstyle='round,pad=.01,rounding_size=.025',transform=ax.transAxes,fc=CARD,ec=PINK,lw=2)
    ax.add_patch(frame)
    pill=FancyBboxPatch((.31,.835),.375,.055,boxstyle='round,pad=.008,rounding_size=.015',transform=ax.transAxes,fc=PINK,ec='none')
    ax.add_patch(pill); ax.text(.497,.862,'TIER 1 VERIFIER CIRCUIT BREAKER',transform=ax.transAxes,ha='center',va='center',fontsize=9,color=BG,fontweight='bold')
    ax.text(.497,.815,'TEMP = 0.0 (100% Deterministic Audit)',transform=ax.transAxes,ha='center',color=AMBER,fontsize=8.4,fontweight='bold')
    gate_specs=[
      ('GATE 1 // NETWORK & TIMEOUT GUARD',[('Pass: HTTP 200 OK (< 15s Prod Cap)',GREEN),('Fault Injected: 1ms ETIMEDOUT Outage',WHITE),('Trap: VERIFIER_HTTP_ERROR_FAIL_CLOSED',PINK)]),
      ('GATE 2 // STRICT JSON PARSER',[('Pass: JSON.parse().verification_passed === true',GREEN),('Fault Injected: Substring Spoof & Truncated JSON',WHITE),("Blocks naive .includes('true') bypasses",PINK)]),
      ('GATE 3 // TEMPORAL & SLA AUDIT',[('Pass: Active Policy (Ref: Nov 9, 2026) + Exact SLA',GREEN),('Fault Injected: Expired 2024 Waiver & 48h Hallucination',WHITE),('Trap: EXPIRED_OR_INACTIVE_POLICY (HOLD-033)',PINK)])]
    ys=[.665,.425,.185]
    for (title,lines),y in zip(gate_specs,ys):
        box(ax,(.30,y),.395,.19,title,lines,PINK,fontsize=7.0,title_size=7.6)
    # outcomes on right; arrows cleanly bridge central frame/right
    ax.text(.76,.81,'ALL 3 PASS',transform=ax.transAxes,ha='center',color=GREEN,fontsize=8.5,fontweight='bold')
    ax.add_patch(FancyArrowPatch((.725,.76),(.775,.76),transform=ax.transAxes,arrowstyle='-|>',mutation_scale=15,color=GREEN,lw=2))
    box(ax,(.78,.59),.195,.28,'TIER 1 AUTO-DISPATCH',[
      ('Verified Customer Send',WHITE),('• Precision: 88.9% (Holdout)',GREEN),('• Target SLA: < 5 Seconds',WHITE),('• Unit Cost: $0.003 / ticket',AMBER)],GREEN,fontsize=7.6,title_size=7.4)
    ax.text(.76,.47,'ANY GATE TRIPS!',transform=ax.transAxes,ha='center',color=PINK,fontsize=8.5,fontweight='bold')
    ax.add_patch(FancyArrowPatch((.725,.43),(.775,.43),transform=ax.transAxes,arrowstyle='-|>',mutation_scale=15,color=PINK,lw=2))
    box(ax,(.78,.15),.195,.28,'SINGLE-HOP DOWNGRADE',[
      ('Tier 2 Agent Copilot Queue',WHITE),('SYNTHESIS TEMP = 0.1',AMBER),('• Surfaces Top-3 Sibling Codes',WHITE),('• Target SLA: < 15 Minutes',WHITE),('• Unit Cost: $1.50 / review',AMBER),('• Leaks: 0% Hallucinations',PINK)],PINK,fontsize=6.7,title_size=7.3)
    # economics strip across bottom inside main frame
    strip=FancyBboxPatch((.035,.025),.94,.075,boxstyle='round,pad=.008,rounding_size=.012',transform=ax.transAxes,fc=CARD,ec='#393047',lw=1)
    ax.add_patch(strip)
    pill2=FancyBboxPatch((.40,.063),.20,.027,boxstyle='round,pad=.004,rounding_size=.01',transform=ax.transAxes,fc=PINK,ec='none')
    ax.add_patch(pill2); ax.text(.50,.076,'OPERATIONAL ECONOMICS & SLA MAP',transform=ax.transAxes,ha='center',va='center',fontsize=6.8,color=BG,fontweight='bold')
    ax.text(.5,.043,'TIER 1 AUTO: $0.003 | < 5s SLA     TIER 2 COPILOT: $1.50 | < 15m SLA     TIER 3 SPECIALIST: $6.00 | < 4h SLA (0 LLM)     DEAD-LETTER: ROUTING_ERROR_FALLBACK',
      transform=ax.transAxes,ha='center',va='center',fontsize=5.7,color=WHITE)
    save(fig,'verifier_circuit_breaker.png')

def main():
    chart1(); chart2(); hero(); chart3()
    print('Generated four 300 DPI PNGs in output root and project assets/')
if __name__=='__main__': main()
