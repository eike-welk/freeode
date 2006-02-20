#!/usr/bin/python

from scipy import * #also includes Numeric
import Gnuplot, Gnuplot.funcutils
import time

#l=linspace(0,1,30) #create array of 30 numbers from 0..1
#A=zeros((n,n), Float); A.shape=(n,n)

#-------------------------------------------------------------------
#define the system object 
class Biofilm:
    """
    A simple biofilm. 
    This class contains the differetial equation by providinges the function 
    y_dot=dy(y,t).
    It stores the pararmeters and initial ?conditions?.
    """
    
    def __init__ (self):
        """ initialize the constants"""
        #constants for the numerical method
        self.nPX = nPX = 21    #Number of grid points
        self.lenX= 0.1   #size of the distribution domain TODO should be upper and lower boundaries
        self.hX   = self.lenX/(self.nPX-1) #Distance between grid points
        #describe layout of variables in state and time derivative vectors
        self.sl_O2   = slice(0, nPX) #[mmol/L]oxygen concentrations
        self.sl_CO2 = slice(1*nPX, 2*nPX) #[mmol/L] the oxygen concentrations
        self.sl_S      = slice(2*nPX, 3*nPX) #[g/L] the substrate concentrations
        self.sl_X      = slice(3*nPX, 4*nPX) #[g/L] the substrate concentrations
        
        #the physical constants
        self.mu_max = 0.32  #[h^-1]
        self.Ks     = 50e-3*90/1000#0.005 #[g/L]
        self.Ko2     = 1e-3 #[mmol/L]
        self.Yxs    = 0.47  #[g(x)/g(s)]
        self.Yxo2   = 0.89*32.0/1000.0 #[g(x)/mmol(O2)]
        self.Ms      = 0.034 #[g(S)/g(X)/h]
        self.Mo2    = 0.034/180.0*1000.0 #[mmol(O2)/g(X)/h]
        self.Ds      = 0.33  *5.1e-6  *1e6   #[mm^2/h] Diffusion constant S
        self.Do2    = 0.634*10.2e-6*1e6   #[mm^2/h] Diffusion constant O2
        self.Dco2  = 0.634*7.8e-6  *1e6   #[mm^2/h] Diffusion constant CO2
##~         self.O2liqu= 0.1 #[mmol/L] oxygen concentration in the liquid phase
        self.CO2liqu= 0.01 #[mmol/L] CO2 concentration in the liquid phase
##~         self.Sliqu   = 5.0 #[mmol/L] substrate concentration in the liquid phase
        #Select limitation regime
        self.O2liqu= 0.1; self.Sliqu   = 0.025 # Thick biofilm - low activity
        #self.O2liqu= 0.1; self.Sliqu   = 0.5  # Thin biofilm - high activity

    def initCond(self):
        """
        Return a state vector (y) which can be used to start the simulation.
        usefull initial conditions.
        """
        c_1=ones(self.nPX,Float)
        y=zeros(self.nPX*4,Float)
##~         y[self.sl_O2][0]=self.O2liqu 
##~         y[self.sl_CO2][0]=self.CO2liqu 
##~         y[self.sl_S][0]=self.Sliqu 
##~         y[self.sl_X]=0.1

        y[self.sl_O2]=c_1*self.O2liqu 
        y[self.sl_CO2]=c_1*self.CO2liqu 
        y[self.sl_S]=c_1*self.Sliqu 
        y[self.sl_X]=c_1*0.1
        
        return y
##~         return array([], Float)

    def dy(self, ySt, t):
        """
        The differetial equation. 
        y: state, t: time
        return: dy/dt
        """
        #create local variables for constants 
        nPX=self.nPX #number of grid points
        hX=self.hX     #distance between grid points
        #describe layout of variables in state and time derivative vectors
        sl_O2 = self.sl_O2; sl_CO2 = self.sl_CO2; sl_S = self.sl_S; sl_X = self.sl_X
       #constants for problem
        mu_max=self.mu_max #[h^-1]
        Ks=self.Ks      #[g/L]
        Ko2=self.Ko2      #[mmol/L]
        Yxs=self.Yxs      #[g(x)/g(s)]
        Yxo2=self.Yxo2    #[g(x)/mmol(O2)]
        Ms=self.Ms       #[g(S)/g(X)/h]
        Mo2=self.Mo2    #[mmol(O2)/g(X)/h]
        Ds=self.Ds         #[mm^2/h] Diffusion constant S
        Do2=self.Do2       #[mm^2/h] Diffusion constant O2
        Dco2=self.Dco2     #[mm^2/h] Diffusion constant CO2
        
        #state variables: get from state vector and put into local variables 
        O2 = ySt[sl_O2] #[mmol/L] the oxygen concentrations
        O2[0] = self.O2liqu #[mmol/L] boundary condition right - fixed concentration
        CO2 = ySt[sl_CO2] #[mmol/L] the oxygen concentrations
        CO2[0] = self.CO2liqu #[mmol/L] boundary condition right - fixed concentration
        S = ySt[sl_S] #[g/L] the substrate concentrations
        S[0] = self.Sliqu #[g/L] boundary condition right - fixed concentration
        X = ySt[sl_X] #[g/L] the substrate concentrations
        
        #1st derivatives: Introduce boundary condition when 1st derivatives (Sx, O2x, CO2x) are not computed
        S[nPX-1]=S[nPX-2] # Sx[nPX-1]=0 -- no diffusion at right boundary
        O2[nPX-1]=O2[nPX-2] # Sx[nPX-1]=0 -- no diffusion at right boundary
        CO2[nPX-1]=CO2[nPX-2] # Sx[nPX-1]=0 -- no diffusion at right boundary
       
        #2nd derivatives: Compute 2nd the derivatives
        O2xx = zeros(nPX, Float)
        O2xx[1:nPX-1] = (O2[2:nPX]-2.0*O2[1:nPX-1]+O2[0:nPX-2])/hX**2 # diff(O2, x, x) without boundaries
        O2xx[nPX-1]=(O2[nPX-1]-2*O2[nPX-2]+O2[nPX-3])/hX**2 #backward difference at right boundary 
        CO2xx = zeros(nPX, Float)
        CO2xx[1:nPX-1] = (CO2[2:nPX]-2.0*CO2[1:nPX-1]+CO2[0:nPX-2])/hX**2 # diff(CO2, x, x) without boundaries
        CO2xx[nPX-1]=(CO2[nPX-1]-2*CO2[nPX-2]+CO2[nPX-3])/hX**2 #backward difference at right boundary 
        Sxx = zeros(nPX, Float)
        Sxx[1:nPX-1] = (S[2:nPX]-2.0*S[1:nPX-1]+S[0:nPX-2])/hX**2 # diff(S, x, x) without boundaries
        Sxx[nPX-1]=(S[nPX-1]-2*S[nPX-2]+S[nPX-3])/hX**2 #backward difference at right boundary 
        
        #compute algebraic variables
##~         mu=zeros(nPX, Float)
        mu=mu_max * min(select([S>0],[S/(S+Ks)]), select([O2>0],[O2/(O2+Ko2)]))
##~         print mu
##~         c_0=zeros(nPX, Float)
        
        #the differetial equations
        y_dot = zeros(4*nPX, Float) #create array for all time derivatives 
        y_dot[sl_O2][1:nPX-1]   = self.Do2*O2xx[1:nPX-1] - (mu[1:nPX-1]*X[1:nPX-1])/Yxo2 - Mo2*X[1:nPX-1] #O2
        y_dot[sl_CO2][1:nPX-1] = self.Dco2*CO2xx[1:nPX-1] #CO2
        y_dot[sl_S][1:nPX-1]      = self.Ds*Sxx[1:nPX-1]  - (mu[1:nPX-1]*X[1:nPX-1])/Yxs - Ms*X[1:nPX-1] #S
        y_dot[sl_X]                  = mu*X - select([X > 70], [(X-70)*100]) - (select([O2<Ko2/50], [(Ko2/50-O2)*(1e6)]) + select([S<Ks/50], [(Ks/50-S)*1e6]))*X #X
        return y_dot   
        #max(X-70.0,0.0)*100.0
    #ideas: 
    #Functions that get and set the variables from the state array
    #may need state array as member variable. 
    #Benefit: The definition of the slices that hold the state variables 
    #in the state array are only in one place.
    #def getS(self):
    #   return self.y[0:self.nP]
    #
    #Functions to compute the first or second derivative, and take 
    #possible boundary conditions into account by using forward and 
    #backward differences
    #
    #Monte carlo function to discover different steady state solutions 
    #by trying random start values 
    
    
#-----------------------------------
def solve_dynamic():
    """find dynamic solution by integration of the system"""
    t1=time.time()
    print "starting dynamic simulation"
    
    sys=Biofilm()
    y0=sys.initCond()
    t=linspace(0, 100, 150)
    
    y=integrate.odeint(sys.dy, y0, t)
    
    t2=time.time()
    print "Time for integratetion [s]: %g" % (t2-t1)
    
    #-------------------------------------
    #plot results
    xVals=linspace(0, sys.lenX, sys.nPX) # numbers for x-Axis
    
    #plot oxygen
    gO2=Gnuplot.Gnuplot(debug=0)
    gO2('set parametric')
    gO2('set data style lines')
    gO2('set hidden')
    gO2('set contour base')
    title='Oxygen'
    gO2.title(title)
    gO2.xlabel('t')
    gO2.ylabel('x') 
    gO2.splot(Gnuplot.GridData(y[:,sys.sl_O2],t,xVals, binary=1))
    #gO2.hardcopy(title+'.ps', enhanced=1, color=1)
   
    ##~ #plot CO2
    ##~ gCO2=Gnuplot.Gnuplot(debug=0)
    ##~ gCO2('set parametric')
    ##~ gCO2('set data style lines')
    ##~ gCO2('set hidden')
    ##~ gCO2('set contour base')
    ##~ title='CO2'
    ##~gCO2.title(title)
    ##~ gCO2.xlabel('t')
    ##~ gCO2.ylabel('x') 
    ##~ gCO2.splot(Gnuplot.GridData(y[:,sys.sl_CO2],t,xVals, binary=1))
    ##~gCO2.hardcopy(title+'.ps', enhanced=1, color=1)

    #plot Substrate
    gS=Gnuplot.Gnuplot(debug=0)
    gS('set parametric')
    gS('set data style lines')
    gS('set hidden')
    gS('set contour base')
    title='Substrate'
    gS.title(title)
    gS.xlabel('t')
    gS.ylabel('x') 
    gS.splot(Gnuplot.GridData(y[:,sys.sl_S],t,xVals, binary=1))
    #gS.hardcopy(title+'.ps', enhanced=1, color=1)
    
    #plot biomass
    gX=Gnuplot.Gnuplot(debug=0)
    gX('set parametric')
    gX('set data style lines')
    gX('set hidden')
    gX('set contour base')
    title='Biomass'
    gX.title(title)
    gX.ylabel('x') 
    gX.splot(Gnuplot.GridData(y[:,sys.sl_X],t,xVals, binary=1))
    #gX.hardcopy(title+'.ps', enhanced=1, color=1)
    
    #plot mu
    gmu=Gnuplot.Gnuplot(debug=0)
    gmu('set parametric')
    gmu('set data style lines')
    gmu('set hidden')
    gmu('set contour base')
    title='Mu'
    gmu.title(title)
    gmu.xlabel('t')
    gmu.ylabel('x') 
    mu=sys.mu_max * min(select([y[:,sys.sl_S]>0],[y[:,sys.sl_S]/(y[:,sys.sl_S]+sys.Ks)]), select([y[:,sys.sl_O2]>0],[y[:,sys.sl_O2]/(y[:,sys.sl_O2]+sys.Ko2)]))
    gmu.splot(Gnuplot.GridData(mu,t,xVals, binary=1))
    #gmu.hardcopy(title+'.ps', enhanced=1, color=1)
    
    ##~ #plot all state variables into one diagram
    ##~ g=Gnuplot.Gnuplot(debug=0)
    ##~ g('set parametric')
    ##~ g('set data style lines')
    ##~ g('set hidden')
    ##~ g('set contour base')
    ##~ g.title('Dynamic Diffusion')
    ##~ g.xlabel('t')
    ##~ g.ylabel('x') 
    ##~ xValsAll=linspace(0, sys.lenX*4, sys.nPX*4)
    ##~ g.splot(Gnuplot.GridData(y,t,xValsAll, binary=1))
    
    raw_input('Please press return to continue...\n')
    
    return y
    
    
#--------------------------------------------------------
def solve_steadystate():
    """compute steady state solutions at different values for the substrate concentration Sliqu"""
    t1=time.time()
    print "starting steady state simulation"
 
    sys=Biofilm() # the biofilm object
 
    def residualF(y):
        """wrapper function for the root finder - evaluate y_dot at t=0"""
        return sys.dy(y, 0)
    
    sequSliqu=linspace(0.001,  0.5, 50) #the substrate concentrations  I want to evaluate
    index=arange(0,len(sequSliqu)) #index to access sequence
    yStart=sys.initCond()+0.0 #the start value
    ySt=zeros([len(sequSliqu), len(yStart)], Float) #the steady state solutions go here
    
    #find the steady state at each D
    for Sliqu, i in zip(sequSliqu, index):
        sys.Sliqu=Sliqu
        ySt[i]=optimize.fsolve(residualF, yStart)# r.initCond())
##~         yStart=ySt[i] #use last solution as next start value
##~         print i
    
    t2=time.time()
    print "Time for steady state solution [s]: %g" % (t2-t1)
    
    #plot the results
    xVals=linspace(0, sys.lenX, sys.nPX) # numbers for x-Axis
    
    #plot oxygen
    gO2=Gnuplot.Gnuplot(debug=0)
    gO2('set parametric')
    gO2('set data style lines')
    gO2('set hidden')
    gO2('set contour base')
    gO2.title('Oxygen')
    gO2.xlabel('S')
    gO2.ylabel('x') 
    gO2.splot(Gnuplot.GridData(ySt[:,sys.sl_O2],sequSliqu,xVals, binary=1))
    
    ##~ #plot CO2
    ##~ gCO2=Gnuplot.Gnuplot(debug=0)
    ##~ gCO2('set parametric')
    ##~ gCO2('set data style lines')
    ##~ gCO2('set hidden')
    ##~ gCO2('set contour base')
    ##~ gCO2.title('CO2')
    ##~ gCO2.xlabel('t')
    ##~ gCO2.ylabel('x') 
    ##~ gCO2.splot(Gnuplot.GridData(ySt[:,sys.sl_CO2],sequSliqu,xVals, binary=1))
    
    #plot Substrate
    gS=Gnuplot.Gnuplot(debug=0)
    gS('set parametric')
    gS('set data style lines')
    gS('set hidden')
    gS('set contour base')
    gS.title('Substrate')
    gS.xlabel('S')
    gS.ylabel('x') 
    gS.splot(Gnuplot.GridData(ySt[:,sys.sl_S],sequSliqu,xVals, binary=1))
    
    #plot biomass
    gX=Gnuplot.Gnuplot(debug=0)
    gX('set parametric')
    gX('set data style lines')
    gX('set hidden')
    gX('set contour base')
    gX.title('Biomass')
    gX.xlabel('S')
    gX.ylabel('x') 
    gX.splot(Gnuplot.GridData(ySt[:,sys.sl_X],sequSliqu,xVals, binary=1))
    
    #plot mu
    gmu=Gnuplot.Gnuplot(debug=0)
    gmu('set parametric')
    gmu('set data style lines')
    gmu('set hidden')
    gmu('set contour base')
    gmu.title('mu')
    gmu.xlabel('S')
    gmu.ylabel('x') 
    mu=sys.mu_max * min(select([ySt[:,sys.sl_S]>0],[ySt[:,sys.sl_S]/(ySt[:,sys.sl_S]+sys.Ks)]), select([ySt[:,sys.sl_O2]>0],[ySt[:,sys.sl_O2]/(ySt[:,sys.sl_O2]+sys.Ko2)]))
    gmu.splot(Gnuplot.GridData(mu,sequSliqu,xVals, binary=1))
    
    ##~ #plot all state variables into one diagram
    ##~ g=Gnuplot.Gnuplot(debug=0)
    ##~ g('set parametric')
    ##~ g('set data style lines')
    ##~ g('set hidden')
    ##~ g('set contour base')
    ##~ g.title('Dynamic Diffusion')
    ##~ g.xlabel('t')
    ##~ g.ylabel('x') 
    ##~ xValsAll=linspace(0, sys.lenX*4, sys.nPX*4)
    ##~ g.splot(Gnuplot.GridData(ySt,sequSliqu,xValsAll, binary=1))

    raw_input('Please press return to continue...\n')

    return ySt
 

solve_dynamic()
#solve_steadystate()



