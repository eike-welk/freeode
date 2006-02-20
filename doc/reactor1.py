#!/usr/bin/python
#---------------------------------------------------------------------
# This hand written simulation program is included here as refference.
#
# This simulation was a first step of the compiler writing process.
# It showed me, that simulation programs could be generated in a quite
# mechanial manner
#---------------------------------------------------------------------

from scipy import * #also includes Numeric
import Gnuplot, Gnuplot.funcutils

#l=linspace(0,1,30) #create array of 30 numbers from 0..1
#A=zeros((n,n), Float); A.shape=(n,n)

#-------------------------------------------------------------------
#define the system object
class Reactor:
    """
    A simple bioreactor.
    This class contains the differetial equation by providinges the function
    y_dot=dy(y,t).
    It stores the pararmeters and initial ?conditions?.
    """

    def __init__(self):
        """ initialize the constants"""
        self.mu_max = 0.32  #[h^-1]
        self.Ks     = 0.005 #[g/L]
        self.Yxs    = 0.47  #[g(x)/g(s)]
        self.maint  = 0.034 #[g/g/h]
        self.D      = 0.2   #[1/h]
        self.Sf     = 5     #[g/L]

    def initCond(self):
        """return usefull initial conditions. return: [S0, X0]"""
        return array([5, 0.1], Float)
        #return array([self.Ks/10, self.Sf*self.Yxs], Float)

    def dy(self, y, t):
        """
        The differential equation.
        y: state S=y[0];  X=Y[1]
        t: time
        return: [dS, dX]
        """
        S=y[0];  X=y[1] #make function look better
        Sf=self.Sf
        #Sf=self.Sf+cos(0.5*t)
        mu = self.mu_max*S/(S+self.Ks) #the growth rate
        dS = (Sf-S)*self.D - 1.0/self.Yxs*mu*X-self.maint*X
        dX = -X*self.D + mu*X
        return array([dS, dX],Float)


#-----------------------------------
#find dynamic solution by integration of the system
r=Reactor()
y0=r.initCond()
t=linspace(0,50,100)

y=integrate.odeint(r.dy, y0, t)

#plot the results
g=Gnuplot.Gnuplot(debug=0)
g.title('Dynamic Simulation')
#g('set data style linespoints')
g('set data style lines')
d0=Gnuplot.Data(t, y[:,0])
d1=Gnuplot.Data(t, y[:,1])
g.plot(d0,d1)

#--------------------------------------------------------
#compute steady state solutions at diferent values for D
def residualF(y):
    """wrapper function for the root finder - evaluate y_dot at t=0"""
    return r.dy(y, 0)

sequD=linspace(0.01, 0.35, 100) #the dilution rates  I want to evaluate
index=arange(0,len(sequD)) #index to access ySt
ySt=zeros([len(sequD),2], Float) #the steady state solutions go here
yStart=array([0,100.0]) #the start value

#find the steady state at each D
for D, i in zip(sequD, index):
    r.D=D
    ySt[i]=optimize.fsolve(residualF, yStart)# r.initCond())
    yStart=ySt[i] #use last solution as next start value
    #print i

#plot X-D Diagram
gSt=Gnuplot.Gnuplot(debug=0)
gSt.title('X-D Diagram - Steady State Simulation')
gSt('set data style lines')
dSt0=Gnuplot.Data(sequD, ySt[:,0])
dSt1=Gnuplot.Data(sequD, ySt[:,1])
gSt.plot(dSt0, dSt1)
