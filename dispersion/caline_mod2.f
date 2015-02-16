! Versione modificata del modello "Caline3 A Versatile Dispersion Model for Predicting Air Pollutant Levels Near Highways and Arterial Streets "
! sviluppato dal CALTEC (California Department of Transportation)
! scaricabile all'indirizzo http://www.epa.gov/scram001/dispersion_prefrec.htm
!
! Versione modificata da CISMA srl all'interno del progetto Integreen
! Gianluca Antonacci
! Ilaria Todeschini
! 02/02/2015

! compilare con il comando
! gfortran -O3 -o caline_mod caline_mod.f

      PROGRAM CALINE_MOD

      IMPLICIT NONE
      INTEGER NRS,NLS,NMAS
      PARAMETER(NRS=80000,NLS=2000,NMAS=100)
      INTEGER CLAS,FLAG1,NRC,IFLAG,IL,NR,NL,IM,NM,I,J,IR,IARGC,CK,NMA
      CHARACTER*2 AG,DP,FL,BR,PS,TYP,TYPL
      CHARACTER*512 FILEIN,FILEOU,FILELO
      CHARACTER*20 RUN,INQ,LNK,VERBOSITY
      LOGICAL VERBOSE
      REAL NE,KZ,LB,LBRG,INC,MIXH,H1,L1,XL1L,XL2L,YL1L,YL2L,MOWT,
     *     D,LL,PI,ED2,FINI,ED1,DWL,UWL,H,HL,YL1,YL2,XL1,XL2,
     *     W,WL,EF,EFL,FF,C,XR,YR,ZR,AMB,VD1,Z0,BRG1,
     *     ATIM,VS1,U,SZ10,HDS,W2,DSTR,FACT,RAD,XVEC,YVEC,PY2,PY1,
     *     BRG,SGN,VD,VS,V1,DREF,PZ1,PZ2,CSL2,QE,FET,YE,SGZ,SGY,
     *     ECLD,Q1,PHI,EN2,EM2,FAC1,FAC2,FAC3,FAC4,FAC5,Z,ARG,ELL2,
     *     XRR,YRR,ZRR,DEG,FPPM,BASE,STP,XMA,YMA,X0R,Y0R,DXR,DYR
      PARAMETER(PI=3.1415926)
      DIMENSION C(NLS,NRS),XR(NRS),YR(NRS),ZR(NRS),XL1(NLS),XL2(NLS),
     *    YL1(NLS),YL2(NLS),EFL(NLS),HL(NLS),WL(NLS),
     *    TYP(NLS),LNK(NLS),LBRG(NLS),LL(NLS),XMA(NMAS),YMA(NMAS)
      DATA AG,DP,FL,BR,PS/'AG','DP','FL','BR','PS'/

      IF (IARGC().LT.3) THEN
         PRINT*,'Command usage:'
         PRINT*,'caline <infile> <outfile> <logfile> <verbosity> '
         PRINT*,'verbosity TRUE O FALSE opzionale> '
         STOP
      ELSEIF(IARGC().EQ.4) THEN
         CALL GETARG(4,VERBOSITY)
      ENDIF
      IF (VERBOSITY .EQ.'T' .OR. VERBOSITY .EQ.'TRUE' 
     * .OR. VERBOSITY .EQ.'true' .OR. VERBOSITY .EQ.'t'
     * .OR. VERBOSITY .EQ.'True') THEN
         VERBOSE=.TRUE.
      ELSE
         VERBOSE=.FALSE.
      ENDIF
      CALL GETARG(1,FILEIN)
      CALL GETARG(2,FILEOU)
      CALL GETARG(3,FILELO)
      IF(VERBOSE) PRINT*,'+-------------------------+'
      IF(VERBOSE) PRINT*,'| Modified CALINE version |'
      IF(VERBOSE) PRINT*,'|     INTEGREEN 2015      |'
      IF(VERBOSE) PRINT*,'+-------------------------+'
      OPEN(1,FILE=FILEIN,STATUS='OLD')
      OPEN(2,FILE=FILEOU)
      OPEN(3,FILE=FILELO)
      XR=0.
      YR=0.
      ZR=0.
      C=0.
      CALL INIT2(RUN,ATIM,Z0,VS,VD,NR,VS1,VD1,XR,YR,ZR,INQ,NL,
     *                 NM,LNK,TYP,XL1,XL2,YL1,YL2,EFL,HL,WL,LL,
     *                 FLAG1,V1,NRC,MOWT,NMA,XMA,YMA,X0R,Y0R,DXR,DYR,
     *                 VERBOSE)
      IF (NR>NRS) THEN
         IF(VERBOSE) WRITE(*,*) 'Allocation error: NR=',NR,' > NRS=',NRS
         STOP
      ENDIF
!     NL= numero di links
      IF (NL>NLS) THEN
         IF(VERBOSE) WRITE(*,*) 'Allocation error: NL=',NL,' > NLS=',NLS
         STOP
      ENDIF
      IF (NMA>NMAS) THEN
         IF(VERBOSE) 
     *     WRITE(*,*) 'Allocation error: NMA=',NMA,' > NMAS=',NMAS
         STOP
      ENDIF
      CALL INIT(MOWT,PI,RAD,DEG,FPPM,DREF)
      WRITE(2,'(A5,5X,I4)') 'ncols        ',NRC
      WRITE(2,'(A5,5X,I4)') 'nrows        ',NR/NRC
      WRITE(2,'(A9,1X,F10.2)') 'xllcorner    ',X0R
      WRITE(2,'(A9,1X,F10.2)') 'yllcorner    ',Y0R-DYR*NR/NRC
      WRITE(2,'(A8,2X,F10.4)') 'cellsize     ',DXR
      WRITE(2,'(A12,1X,F7.0)') 'nodata_value ',0.0
      DO IM=1,NM
         CALL INIT3(DREF,Z0,U,BRG,CLAS,MIXH,AMB,BRG1,RAD,
     *                 XVEC,YVEC,ATIM,PY1,PY2,SZ10,FF,VERBOSE)
         DO I=1,NL
            DO J=1,NR
               C(I,J)=0.
            ENDDO
         ENDDO
         DO IL=1,NL
            IF (VERBOSE) PRINT*, 'LINK',IL
            CALL LINKI(IL,EFL,EF,WL,W,LL,L1,TYPL,TYP,
     *                 XL2,XL2L,XL1,XL1L,YL2,YL2L,YL1,YL1L,HL,H,FL,DP)
            H1=HL(IL)
            CALL LINKL(EF,H1,W,XL2L,XL1L,YL2L,YL1L,L1,
     *                BRG,DEG,RAD,U,DREF,SZ10,ATIM,
     *                HDS,DSTR,PZ1,PZ2,LB,BASE,PHI,Q1,W2)
            LBRG(IL)=LB
C           *****  RECEPTOR LOOP  *****
            DO IR=1,NR
               XRR=XR(IR)
               YRR=YR(IR)
               ZRR=ZR(IR)
               CALL CHECK(XRR,YRR,CK,NMA,XMA,YMA)
               IF (CK.EQ.0) THEN
                   C(IL,IR) = -1.
                   GOTO 6000
               ENDIF
               CALL RECP(XRR,YRR,ZRR,XL2L,XL1L,YL2L,YL1L,L1,H1,
     *                   TYPL,W2,AG,BR,XVEC,YVEC,
     *                   Z,UWL,DWL,D)
               SGN=1.
C              ***  DETERMINES DIRECTION ALONG LINK
C              +1 --> UPWIND ELEMENTS;  -1 --> DOWNWIND ELEMENTS
               NE=0.
               STP=1.
               FINI=1.
               IF (SGN.EQ.1. .AND. UWL.LE.0. .AND. DWL.LT.0.) SGN=-1.
3080           IF (SGN.EQ.-1. .AND. UWL.GT.0. .AND. DWL.GE.0.) GOTO 6000
               ED1=0.
               ED2=SGN*W
C              INITIALIZATION OF ELEMENT LIMITS
3110           CONTINUE
               CALL INITELEM(SGN,UWL,DWL,ED1,ED2,FINI,NE,IFLAG)
               IF (IFLAG .EQ. 1) GOTO 3770
               CALL ELEM(ED2,ED1,W2,PHI,CSL2,EM2,EN2,ELL2,ECLD)
               CALL RECP2(Q1,CSL2,W2,PHI,ECLD,D,FET,YE,QE)
               IF (FET.LE.-CSL2) GOTO 3830
C              ELEMENT DOES NOT CONTRIBUTE
               CALL CFAC1(FET,CSL2,QE,U,SGY,SGZ,PY1,PY2,PZ1,PZ2,FAC1,KZ)
               CALL CFAC2(YE,EN2,EM2,ELL2,SGY,QE,FAC2)
               FACT=FAC1*FAC2
C              *****  DEPRESSED SECTION  *****
               CALL DEPRESSED(HDS,D,W2,DSTR,FACT)
C              *****  DEPOSITION CORRECTION  *****
               CALL CFAC3(V1,SGZ,KZ,Z,H,PI,FAC3,ARG)
               IF (ARG.GT.5.) GOTO 3770
C              *****  SETTLING CORRECTION  *****
               CALL CFAC4(VS,Z,H,SGZ,KZ,FAC4)
               FACT=FACT*FAC4
C              *****  INCREMENTAL CONCENTRATION  *****
               CALL CFAC5(Z,H,MIXH,SGZ,FAC5)
               INC=FACT*(FAC5-FAC3)
               C(IL,IR)=C(IL,IR)+INC
3770           IF (FINI.EQ.0.) GOTO 6000
               NE=NE+1.
               STP=BASE**NE
               IF (NE.EQ.0.) GOTO 3080
               ED1=ED2
               ED2=ED2+SGN*STP*W
C              INCREMENT TO NEXT ELEMENT
               GOTO 3110
3830           IF (SGN.EQ.1.) GOTO 3770
6000           CONTINUE
            ENDDO
         ENDDO
         CALL MG2PPM(NL,NR,FPPM,C,NLS)
         CALL OUTPUT(INQ,U,CLAS,VS1,MIXH,NL,NR,
     *               BRG1,Z0,VD1,AMB,C,NLS,NRC,FF)
      ENDDO

      CLOSE(1)
      CLOSE(2)
      CLOSE(3)

      STOP
      END


c----------------------------------------------------------------------------------


      SUBROUTINE MG2PPM(NL,NR,FPPM,C,NLS)
C        CONCENTRATION FROM MICROGRAMS/M**3 TO PPM
         IMPLICIT NONE
         INTEGER NLS,I,J,NR,NL
         REAL C,FPPM
         DIMENSION C(NLS,*)

         DO I=1,NL
            DO J=1,NR
               C(I,J)=C(I,J)*FPPM
            ENDDO
         ENDDO

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE INIT(MOWT,PI,RAD,DEG,FPPM,DREF)
C        INITIALIZATION OF CONSTANTS AND COUNTERS
         IMPLICIT NONE
         REAL PI,RAD,DEG,FPPM,DREF,MOWT

         RAD=PI/180.
         DEG=180./PI
         IF (MOWT .EQ. 0.) THEN
            FPPM = 1.
         ELSE
            FPPM=0.0245/MOWT
         ENDIF
         DREF=ALOG(10000.)

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE LINKL(EF,H1,W,XL2L,XL1L,YL2L,YL1L,L1,
     *                BRG,DEG,RAD,U,DREF,SZ10,ATIM,
     *                HDS,DSTR,PZ1,PZ2,LB,BASE,PHI,Q1,W2)

         IMPLICIT NONE
         REAL EF,H1,W,DEG,RAD,HDS,DSTR,PZ1,PZ2,Q1,U,W2,PHI,BASE,LB,
     *        SGZ1,TR,DREF,SZ10,ATIM,BRG,ABSXD,XD,YD,L1,XL2L,XL1L,YL2L,
     *        YL1L

         XD=XL2L-XL1L
         YD=YL2L-YL1L
         W2=W/2.
         Q1=0.2777778*EF !!! SE SI USA FATTORE EMISSIONE IN G/KM
C        LINEAL SOURCE STRENGTH PARALLEL TO HIGHWAY IN MICRO-GRAMS/(METER*SEC)
         ABSXD=ABS(XD)
         IF(ABSXD.GT.L1) L1=ABSXD
         LB=DEG*(ACOS(ABS(XD)/L1))
C        LINK BEARING
         IF (XD.GT.0. .AND. YD.GE.0.) LB=90.-LB
         IF (XD.GE.0. .AND. YD.LT.0.) LB=90.+LB
         IF (XD.LT.0. .AND. YD.LE.0.) LB=270.-LB
         IF (XD.LE.0. .AND. YD.GT.0.) LB=270.+LB
C        LINK BEARING MATRIX FOR OUTPUT
         PHI=ABS(BRG-LB)
C        WIND ANGLE WITH RESPECT TO LINK
         IF (PHI.LE.90.) THEN
            CONTINUE
         ELSEIF (PHI.GE.270.) THEN
            PHI=ABS(PHI-360.)
         ELSE
            PHI=ABS(PHI-180.)
         ENDIF
C        SET ELEMENT GROWTH BASE
         IF (PHI.LT.20.) THEN
            BASE=1.1
         ELSEIF (PHI.LT.50.) THEN
            BASE=1.5
         ELSEIF (PHI.LT.70.) THEN
            BASE=2.
         ELSE
            BASE=4.
         ENDIF
         PHI=RAD*PHI
C        CONVERSION OF PHI FROM DEGREES TO RADIANS
         IF (PHI.GT.1.5706) PHI=1.5706
         IF (PHI.LT.0.00017) PHI=0.00017
C        DEPRESSED SECTION
         IF (H1.LT.-1.5) THEN
            HDS=H1
            DSTR=0.72*ABS(HDS)**0.83
         ELSE
            DSTR=1.
            HDS=1.
         ENDIF
C        RESIDENCE TIME FACTOR
C        SIGMA Z POWER CURVE
         TR=DSTR*W2/U
         SGZ1=ALOG((1.8+0.11*TR)*(ATIM/30.)**0.2)
         PZ2=(SZ10-SGZ1)/(DREF-ALOG(W2))
         PZ1=EXP((SZ10+SGZ1-PZ2*(DREF+ALOG(W2)))/2.)

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE RECP(XRR,YRR,ZRR,XL2L,XL1L,YL2L,YL1L,L1,H1,
     *                TYPL,W2,AG,BR,XVEC,YVEC,
     *                Z,UWL,DWL,D)

         IMPLICIT NONE
         CHARACTER*2 TYPL,AG,BR
         REAL UWL,DWL,Z,XRR,YRR,ZRR,W2,D2,D1,H1,TEMP,XVEC,YVEC,XL1L,
     *        XL2L,YL1L,YL2L,DVIR,A,B,L,L1,D,APRI,BPRI,DPRI,XPRI,YPRI,
     *        LPRI

         A=(XRR-XL1L)**2+(YRR-YL1L)**2
         B=(XRR-XL2L)**2+(YRR-YL2L)**2
         L=(B-A-L1**2)/(2.*L1)
C        OFFSET LENGTH
         IF (A.GT.L**2) THEN
            D=SQRT(A-L**2)
         ELSE
            D=0.
         ENDIF
C        RECEPTOR DISTANCE
         UWL=L1+L
C        UPWIND LENGTH
         DWL=L
C        DOWNWIND LENGTH
         IF(D.EQ.0.) THEN
            DVIR=1.
         ELSE
            DVIR=D
         ENDIF
         XPRI=XRR+DVIR*XVEC
         YPRI=YRR+DVIR*YVEC
         APRI=(XPRI-XL1L)**2+(YPRI-YL1L)**2
         BPRI=(XPRI-XL2L)**2+(YPRI-YL2L)**2
         LPRI=(BPRI-APRI-L1**2)/(2.*L1)
         IF (APRI.GT.LPRI**2) THEN
            DPRI=SQRT(APRI-LPRI**2)
         ELSE
            DPRI=0.
         ENDIF
         IF (DPRI.LT.D) D=-D
         IF (LPRI-L .LT. 0) THEN
            TEMP=UWL
            UWL=-DWL
            DWL=-TEMP
         ENDIF
         IF (TYPL.EQ.AG .OR. TYPL.EQ.BR) THEN
            Z=ZRR
         ELSE
            D1=W2+2.*ABS(H1)
            D2=W2
C           SINGLE PRECISION TO DOUBLE PRECISION FOR LOGICAL 'IF'
            IF (ABS(D).GE.D1) THEN
               Z=ZRR
            ELSEIF (ABS(D).LE.D2) THEN
               Z=ZRR-H1
            ELSE
               Z=ZRR-H1*(1.-(ABS(D)-W2)/(2.*ABS(H1)))
            ENDIF
         ENDIF

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE CFAC2(YE,EN2,EM2,ELL2,SGY,QE,FAC2)

         IMPLICIT NONE
         INTEGER I
         REAL Y,WT,YE,ELL2,EN2,EM2,SGY,LIM,ARG,QE,T,PD,INTG,FAC2
         DIMENSION Y(6),WT(5),INTG(6)
         DATA WT/0.25,0.75,1.,0.75,0.25/

C        ADJUSTMENT FOR ELEMENT END EFFECT
C        (POLYNOMIAL APPROXIMATION)
         Y(1)=YE+ELL2
         Y(2)=Y(1)-EN2
         Y(3)=Y(2)-EN2
         Y(4)=Y(3)-2*EM2
         Y(5)=Y(4)-EN2
         Y(6)=Y(5)-EN2
         DO I=1,6
C        SUB-ELEMENT SOURCE STRENGTH LOOP
            LIM=ABS(Y(I)/SGY)
            T=1./(1.+0.23164*LIM)
            ARG=LIM**2/(-2.)
            IF (LIM.GT.5.) THEN
               INTG(I)=0.
            ELSE
               INTG(I)=0.3989*EXP(ARG)*(0.3194*T-0.3566*T**2+
     *         1.7815*T**3-1.8213*T**4+1.3303*T**5)
            ENDIF
         ENDDO
         FAC2=0.
         DO I=1,5
            IF ((SIGN(1.,Y(I))).EQ.(SIGN(1.,Y(I+1)))) THEN
               PD=ABS(INTG(I+1)-INTG(I))
            ELSE
               PD=1.-INTG(I)-INTG(I+1)
            ENDIF
C           NORMAL PROBABILITY DENSITY FUNCTION
            FAC2=FAC2+PD*QE*WT(I)
         ENDDO
         RETURN
      END SUBROUTINE

c----------------------------------------------------------------------------------

      SUBROUTINE CFAC3(V1,SGZ,KZ,Z,H,PI,FAC3,ARG)

         IMPLICIT NONE
         REAL V1,SGZ,KZ,Z,H,PI,FAC3,ARG,EFRC,T

         FAC3=0.
         IF (V1.NE.0.) THEN
            ARG=V1*SGZ/(KZ*SQRT(2.))+(Z+H)/(SGZ*SQRT(2.))
            IF (ARG.GT.5.) RETURN
            T=1./(1.+0.47047*ARG)
            EFRC=(.3480242*T-.0958798*T**2+.7478556*T**3)*
     *           EXP(-1.*ARG**2)
            FAC3=(SQRT(2.*PI)*V1*SGZ*EXP(V1*(Z+H)/KZ+.5*
     *           (V1*SGZ/KZ)**2)*EFRC)/KZ
            IF (FAC3.GT.2.) FAC3=2.
         ENDIF

         RETURN
      END SUBROUTINE

c----------------------------------------------------------------------------------

      SUBROUTINE CFAC4(VS,Z,H,SGZ,KZ,FAC4)

          IMPLICIT NONE
          REAL VS,Z,H,SGZ,KZ,FAC4

          IF (VS.NE.0.) THEN
              FAC4=EXP(-VS*(Z-H)/(2.*KZ)-(VS*SGZ/KZ)**2/8.)
          ELSE
              FAC4=1.
          ENDIF

         RETURN
      END SUBROUTINE

c----------------------------------------------------------------------------------


      SUBROUTINE CFAC5(Z,H,MIXH,SGZ,FAC5)

         IMPLICIT NONE
         REAL Z,H,MIXH,SGZ,FAC5,CNT,EXLS,ARG1,ARG2,EXP1,EXP2

         FAC5=0.
         CNT=0.
3720     EXLS=0.
3730     ARG1=-0.5*((Z+H+2.*CNT*MIXH)/SGZ)**2
         ARG2=-0.5*((Z-H+2.*CNT*MIXH)/SGZ)**2
         EXP1=EXP(ARG1)
         EXP2=EXP(ARG2)
         FAC5=FAC5+EXP1+EXP2
         IF (MIXH.GE.1000.) RETURN
C        BYPASS MIXING HEIGHT CALCULATION
         IF ((EXP1+EXP2+EXLS).EQ.0. .AND. CNT.LE.0.) RETURN
         IF (CNT.LE.0.) THEN
            CNT=ABS(CNT)+1.
            GOTO 3720
         ELSE
            CNT=-1.*CNT
            EXLS=EXP1+EXP2
            GOTO 3730
         ENDIF

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE ELEM(ED2,ED1,W2,PHI,CSL2,EM2,EN2,ELL2,ECLD)

         IMPLICIT NONE
         REAL ED2,ED1,W2,PHI,CSL2,EM2,EN2,ELL2,EL2,ECLD

         EL2=ABS(ED2-ED1)/2.
         ECLD=(ED1+ED2)/2.
         ELL2=W2/COS(PHI)+(EL2-W2*TAN(PHI))*SIN(PHI)
         IF (PHI.GE.ATAN(W2/EL2)) THEN
            CSL2=W2/SIN(PHI)
         ELSE
            CSL2=EL2/COS(PHI)
         ENDIF
         EM2=ABS((EL2-W2/TAN(PHI))*SIN(PHI))
         EN2=(ELL2-EM2)/2.

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE RECP2(Q1,CSL2,W2,PHI,ECLD,D,FET,YE,QE)

          IMPLICIT NONE
          REAL Q1,CSL2,W2,PHI,ECLD,FET,YE,QE,SIDE,HYP,D
               
          QE=Q1*CSL2/W2
          FET=(ECLD+D*TAN(PHI))*COS(PHI)
          HYP=ECLD**2+D**2
          SIDE=FET**2
          IF (SIDE.GT.HYP) THEN
             YE=0.
          ELSE
             YE=SQRT(HYP-SIDE)
          ENDIF

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE CFAC1(FET,CSL2,QE,U,SGY,SGZ,PY1,PY2,PZ1,PZ2,FAC1,KZ)

         IMPLICIT NONE
         REAL FET,CSL2,QE,U,SGY,SGZ,PY1,PY2,PZ1,PZ2,FAC1,KZ

         IF (FET.LT.CSL2) THEN
C           RECEPTOR WITHIN ELEMENT
            QE=QE*(FET+CSL2)/(2.*CSL2)
            FET=(CSL2+FET)/2.
         ENDIF
         SGZ=PZ1*FET**PZ2
         KZ=SGZ**2*U/(2.*FET)
C        VERTICAL DIFFUSIVITY ESTIMATE
         SGY=PY1*FET**PY2
         FAC1=0.399/(SGZ*U)
         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE INIT2(RUN,ATIM,Z0,VS,VD,NR,VS1,VD1,XR,YR,ZR,INQ,NL,
     *                 NM,LNK,TYP,XL1,XL2,YL1,YL2,EFL,HL,WL,LL,
     *                 FLAG1,V1,NRC,MOWT,NMA,XMA,YMA,X0R,Y0R,DXR,DYR,
     *                 VERBOSE)

         IMPLICIT NONE
         INTEGER NR,NL,NM,K,I,J,NRR,NRC,FLAG1,NLP,NLL,NMA
         CHARACTER*2 TYP
         CHARACTER*20 LNK, RUN, INQ
         REAL XR,YR,ZR,XL1,XL2,YL1,YL2,EFL,HL,WL,Z0,ATIM,XUR,
     *        VS1,VS,VD1,VD,V1,XLL,YLL,DXR,DYR,Z0R,MOWT,LL,EMIS,YUR,
     *        X0R,Y0R,XMA,YMA
         LOGICAL VERBOSE
         DIMENSION XR(*),YR(*),ZR(*),XL1(*),XL2(*),TYP(*),LL(*),
     *             YL1(*),YL2(*),EFL(*),HL(*),WL(*),LNK(*),
     *             XMA(*),YMA(*)

         READ(1,*)
         READ(1,*) RUN
         READ(1,*)
         READ(1,*) INQ
         READ(1,*)
         READ(1,*) FLAG1
         READ(1,*)
         WRITE(3,*) 'Nome simulazione:                  ',RUN
         WRITE(3,*) 'Inquinante:                        ',INQ
         IF (FLAG1 .EQ. 1) THEN 
            READ(1,*) MOWT
            WRITE(3,*) 'Unità di misura:                   PPM'
         ELSE
            READ(1,*)
            MOWT = 0.
            WRITE(3,*) 'Unità di misura:                   µg/m³'
         ENDIF
         READ(1,*)
         READ(1,*) ATIM,Z0
         WRITE(3,*) 'Tempo di media:                   ',ATIM
         WRITE(3,*) 'Scabrezza [cm]:                   ',Z0
         READ(1,*)
         READ(1,*) VS,VD
         WRITE(3,*) 'Velocità di sedimentazione [cm/s]:',VS
         WRITE(3,*) 'Velocità di deposizione [cm/s]:   ',VD
         READ(1,*)
         READ(1,*) DXR,DYR
c----------------------- modificare qui per la maschera
c         READ(1,*)
c         READ(1,*) XLL,YLL
c         READ(1,*)
c         READ(1,*) XUR,YUR
         READ(1,*)
         READ(1,*) NMA
         XLL=1.E10
         YLL=1.E10
         XUR=-1.E10
         YUR=-1.E10
         READ(1,*)
         DO I = 1,NMA
            READ(1,*) XMA(I),YMA(I)
            IF (XMA(I).LT.XLL) XLL=XMA(I)
            IF (YMA(I).LT.YLL) YLL=YMA(I)
            IF (XMA(I).GT.XUR) XUR=XMA(I)
            IF (YMA(I).GT.YUR) YUR=YMA(I)
         ENDDO
c         XLL=INT(XLL/100.)*100.
c         YLL=INT(YLL/100.)*100.
c         XUR=INT(XUR/100.)*100.+100.
c         YUR=INT(YUR/100.)*100.+100.
c----------------------------------------------------------
         NRC=NINT((XUR-XLL)/DXR)
         NRR=NINT((YUR-YLL)/DYR)
         READ(1,*)
         READ(1,*) Z0R
         WRITE(3,*) 'Coordinata llc X [m]:             ',XLL
         WRITE(3,*) 'Coordinata llc Y [m]:             ',YLL
         WRITE(3,*) 'Coordinata urc X [m]:             ',XUR
         WRITE(3,*) 'Coordinata urc Y [m]:             ',YUR
         WRITE(3,*) 'Passo di griglia X [m]:           ',DXR
         WRITE(3,*) 'Passo di griglia Y [m]:           ',DYR
         WRITE(3,*) 'Quota recettori [m]:              ',Z0R
         NR = NRR*NRC
         WRITE(3,*) 'N° colonne recettori:             ',NRC
         WRITE(3,*) 'N° righe recettori:               ',NRR
         WRITE(3,*) 'N° totale recettori:              ',NR
         X0R=XLL
         Y0R=YUR
         DO I = 1,NRR
            DO J = 1,NRC
               K = (I-1)*NRC+J
               XR(K) = X0R+DXR*(J-1)
               YR(K) = Y0R-DYR*(I-1)
               ZR(K) = Z0R
            ENDDO
         ENDDO
         VS1=VS
         VD1=VD
         VS=VS*0.01
         VD=VD*0.01
         V1=VD-VS*0.5
         READ(1,*)
         READ(1,*) NLL
         WRITE(3,*) 'N° sorgenti lineari:               ',NLL
         WRITE(3,*) '------------------------------------------'
         WRITE(3,*) 'Lista sorgenti:'
         WRITE(3,*) 'Nome - Tipo - Lunghezza - Larghezza - Emissione'
         WRITE(3,*) '                 [m]         [m]     [µg/(m²s)]'
         READ(1,*)

!        Section type -- TYP
!          AG=At-Grade
!          FL=Fill
!          BR=Bridge
!          DP=Depressed
!        EFL=emission factor [g/h/km]
!        HL=source height [m]
!        WL=mixing zone width [m]

         DO I=1,NLL
            READ(1,*) LNK(I),TYP(I),XL1(I),YL1(I),XL2(I),
     *                  YL2(I),EFL(I),HL(I),WL(I)
            LL(I)=SQRT((XL1(I)-XL2(I))**2+(YL1(I)-YL2(I))**2)
            IF(VERBOSE) WRITE(*,*) 'Reading link ',LNK(I),'...'
            IF (LL(I).LT.WL(I)) THEN
               IF(VERBOSE) WRITE (*,170)
               IF(VERBOSE) WRITE (*,*) 'Link ',LNK(I)
               IF(VERBOSE) WRITE (*,*) 'Length = ',LL(I),' Width = ',
     *         WL(I)
               LL(I) = WL(I) ! rimuovere dopo aver corretto i punti
!               STOP
            ENDIF
            IF (ABS(HL(I)).GT.10.) THEN
               IF(VERBOSE) WRITE (*,180)
               STOP
            ENDIF
            EMIS = 0.2777778*EFL(I)/LL(I)
            WRITE(3,160) LNK(I),TYP(I),LL(I),WL(I),EMIS
         ENDDO
         READ(1,*)
         READ(1,*) NLP ! sorgenti areali
         WRITE(3,*) 'N° sorgenti areali:                ',NLP
         WRITE(3,*) '------------------------------------------'
         WRITE(3,*) 'Lista sorgenti:'
         WRITE(3,*) 'Nome - Tipo - Lunghezza - Larghezza - Emissione'
         WRITE(3,*) '                 [m]         [m]     [µg/(m²s)]'
         READ(1,*)
         NL = NLL+NLP
         DO I = NLL+1,NL
            READ(1,*) LNK(I),TYP(I),XL1(I),YL1(I),XL2(I),YL2(I),EFL(I),
     *                HL(I),WL(I)
            EFL(I) = 1000.*EFL(I)
            LL(I)=SQRT((XL1(I)-XL2(I))**2+(YL1(I)-YL2(I))**2)
            WRITE(*,*) 'Reading area ',LNK(I),'...'
            IF (ABS(HL(I)).GT.10.) THEN
               IF(VERBOSE) WRITE (*,180)
               STOP
            ENDIF
            EMIS = 0.2777778*EFL(I)/LL(I)
            WRITE(3,160) LNK(I),TYP(I),LL(I),WL(I),EMIS
         ENDDO
         READ(1,*)
         READ(1,*) NM
         WRITE(3,*) '------------------------------------------'
         WRITE(3,*) 'N° scenari meteo: ',NM
         READ(1,*)
160      FORMAT(A20,1X,A2,F8.2,1X,F5.1,1X,F8.4)
170      FORMAT ('Run terminated',/,
     *   'link length must be greater than or equal to link width.')
180      FORMAT ('run terminated',/,
     *   'source must be within 10 meters of datum.')

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE INIT3(DREF,Z0,U,BRG,CLAS,MIXH,AMB,BRG1,RAD,
     *                 XVEC,YVEC,ATIM,PY1,PY2,SZ10,ff,VERBOSE)

         IMPLICIT NONE
         INTEGER CLAS
         REAL U,BRG,MIXH,AMB,BRG1,RAD,XVEC,YVEC,ATIM,PY1,PY2,SZ10,
     *        AFAC,SY1,SY10,Z0,DREF,AZ(6),AY1(6),AY2(6),ff
         LOGICAL VERBOSE
         DATA AZ/1112.,556.,353.,219.,124.,56./
         DATA AY1/0.46,0.29,0.18,0.11,0.087,0.057/
         DATA AY2/1831.,1155.,717.,438.,346.,227./

         READ (1,*) U,BRG,CLAS,MIXH,AMB,FF
         IF (MIXH .LE. 50.) THEN
            IF(VERBOSE) WRITE(*,50)
50          FORMAT ('Hmix <= 50 m: run terminated')
            STOP
         ENDIF
         BRG1=BRG
         BRG=BRG+180.
         IF (BRG.GE.360.) BRG=BRG-360.
         XVEC=COS(RAD*(450.-BRG))
         YVEC=SIN(RAD*(450.-BRG))
         AFAC=(ATIM/3.0)**.2
         SY1=ALOG(AY1(CLAS)*((Z0/3.)**.2)*AFAC)
         SY10=ALOG(AY2(CLAS)*((Z0/3.)**.07)*AFAC)
         PY1=EXP(SY1)
         PY2=(SY10-SY1)/DREF
         SZ10=ALOG(AZ(CLAS)*((Z0/10.)**.07)*AFAC)

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE DEPRESSED(HDS,D,W2,DSTR,FACT)

         IMPLICIT NONE
         REAL HDS,W2,DSTR,FACT,D

         IF (HDS.LT.-1.5 .AND. ABS(D).LT.(W2-3.*HDS)) THEN
            IF (ABS(D).LE.W2) THEN
               FACT=FACT*DSTR
            ELSE
               FACT=FACT*(DSTR-(DSTR-1.)*(ABS(D)-W2)/(-3.*HDS))
            ENDIF
         ENDIF

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE OUTPUT(INQ,U,CLAS,VS1,MIXH,NL,NR,
     *                  BRG1,Z0,VD1,AMB,C,NLS,NRC,FF)

         IMPLICIT NONE
         INTEGER CLAS,NL,NR,I,J,NLS,NRC,JC
         CHARACTER*1 STB
         CHARACTER*20 INQ
         REAL MIXH,C,AMB,BRG1,VD1,Z0,VS1,U,CSUM,CC,FF
         DIMENSION STB(6),C(NLS,*),CC(NRC)
         DATA STB/'A','B','C','D','E','F'/

C         WRITE (2,'(A1,1X,F4.1,1X,F4.0,1X,A1,F6.0)') '#',U,BRG1,
C     *          STB(CLAS),MIXH
C         WRITE (2,'(A1,1X,F4.0,2(1X,F4.1),1X,F5.2)') '#',Z0,
C     *          VS1,VD1,AMB
C        MODEL RESULTS
         JC=0
C         WRITE(2,'(F7.5,1X,A11)') FF,'# frequenza'
         DO I=1,NR
            CSUM=0.
            DO J=1,NL
               IF (C(J,I).GT.0.) CSUM=CSUM+C(J,I)
            ENDDO
            CSUM=CSUM+AMB
C           ADDITION OF AMBIENT
            JC=JC+1
            CC(JC)=CSUM
            IF (JC .EQ. NRC) THEN
!           Alla concentrazione di NOx viene applicata la formula di Romberg per ottenere NO2
               IF ((INQ .EQ. 'NOX') .or. (INQ .EQ. 'NOx') 
     *            .OR. (INQ .EQ. 'nox')) THEN
                  WRITE(2,'(1000(F7.2,1X))') 
     *            ((103*CC(JC)/(CC(JC)+130)+0.005*CC(JC)),JC=1,NRC)
               ELSE
                  WRITE(2,'(1000(F7.2,1X))') (CC(JC),JC=1,NRC)
               ENDIF
               JC=0
            ENDIF
         ENDDO
C         WRITE(2,*)'-----------------------------'
C         WRITE(2,*)
         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE LINKI(IL,EFL,EF,WL,W,LL,L1,TYPL,TYP,
     *                 XL2,XL2L,XL1,XL1L,YL2,YL2L,YL1,YL1L,HL,H,FL,DP)

         IMPLICIT NONE
         INTEGER IL
         CHARACTER*2 DP,FL,TYP,TYPL
         REAL EFL,EF,WL,W,H,HL,XL2,XL1,YL2,YL1,XL2L,XL1L,YL2L,
     *        YL1L,LL,L1
         DIMENSION WL(*),LL(*),XL2(*),XL1(*),YL2(*),YL1(*),
     *             TYP(*),HL(*),EFL(*)

         EF=EFL(IL)
         W=WL(IL)
         XL2L=XL2(IL)
         XL1L=XL1(IL)
         YL2L=YL2(IL)
         YL1L=YL1(IL)
         L1=LL(IL)
         TYPL=TYP(IL)
         IF (TYPL.EQ.DP .OR. TYPL.EQ.FL) THEN
            H=0.
         ELSE
            H=HL(IL)
         ENDIF

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE INITELEM(SGN,UWL,DWL,ED1,ED2,FINI,NE,IFLAG)

         IMPLICIT NONE
         INTEGER IFLAG
         REAL SGN,UWL,DWL,ED1,ED2,FINI,NE

         IFLAG=0
         IF (SGN.EQ.-1.) THEN
            IF (ED1.GE.UWL) THEN
               IF (ED2.GE.UWL) THEN
                  IFLAG=1
                  RETURN
               ENDIF
               ED1=UWL
               IF (ED2.GT.DWL) RETURN
               ED2=DWL
               FINI=0.
            ELSE
               IF (ED2.GT.DWL) RETURN
               ED2=DWL
               FINI=0.
            ENDIF
         ENDIF
         IF (ED1.LE.DWL) THEN
            IF (ED2.LE.DWL) THEN
               IFLAG=1
               RETURN
            ENDIF
            ED1=DWL
            IF (ED2.LT.UWL) RETURN
         ELSE
            IF (ED2.LT.UWL) RETURN
         ENDIF
         ED2=UWL
         SGN=-1.
         NE=-1.

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------


      SUBROUTINE CHECK(XP,YP,CK,NLP,XA,YA)
! controllare qui
         IMPLICIT NONE
         INTEGER LSX,LDX,I,CK,NLP
         REAL X1,Y1,X2,Y2,XP,YP,M,XL,XA,YA
         DIMENSION XA(*),YA(*)

         CK = 0
         LSX = 0
         LDX = 0
         DO I = 1,NLP
            X1 = XA(I)
            Y1 = YA(I)
            IF (I.EQ.NLP) THEN
               X2 = XA(1)
               Y2 = YA(1)
            ELSE
               X2 = XA(I+1)
               Y2 = YA(I+1)
            ENDIF
            IF (
     1         (Y1.EQ.YP .AND. YP.EQ.Y2 .AND. X1.LE.XP .AND. XP.LE.X2)
     2         .OR.
     3         (X1.EQ.XP .AND. XP.EQ.X2 .AND. Y1.LE.YP .AND. YP.LE.Y2)
     4         .OR.
     5         (X1.EQ.XP .AND. Y1.EQ.YP)
     6         .OR.
     7         (X2.EQ.XP .AND. Y2.EQ.YP)
     8         ) THEN
               CK = 1
               RETURN
            ENDIF
            IF ((Y1.LE.YP .AND. YP.LE.Y2) 
     *         .OR. (Y2.LE.YP .AND. YP.LE.Y1)) THEN
               IF (X2.EQ.X1 .AND. X1.LE.XP) THEN
                  LSX = LSX+1
               ELSEIF  (X2.EQ.X1 .AND. X1.GE.XP) THEN
                  LDX = LDX+1
               ELSE
                  M = (Y2-Y1)/(X2-X1)
                  XL = X1-(Y1-YP)/M
                  IF (XL.LT.XP) THEN
                     LSX = LSX+1
                  ELSEIF (XL.GT.XP) THEN
                     LDX = LDX+1
                  ELSE
                     CK = 1
                     RETURN
                  ENDIF
               ENDIF
            ENDIF
         ENDDO
         IF ((MOD(LSX,2) /= 0) .AND. (MOD(LDX,2) /= 0)) THEN
            CK = 1
         ELSE
            CK = 0
         ENDIF

         RETURN
      END SUBROUTINE


c----------------------------------------------------------------------------------
