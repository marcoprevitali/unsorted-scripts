#pragma once
// contactmodelrr_hertz.h

#include "contactmodel/src/contactmodelmechanical.h"

#ifdef RR_HERTZ_LIB
#  define RR_HERTZ_EXPORT EXPORT_TAG
#elif defined(NO_MODEL_IMPORT)
#  define RR_HERTZ_EXPORT
#else
#  define RR_HERTZ_EXPORT IMPORT_TAG
#endif

namespace cmodelsxd {
    using namespace itasca;

    class ContactModelRRHertz : public ContactModelMechanical {
    public:
        enum PropertyKeys {
            kwHzShear = 1
            , kwHzPoiss
            , kwFric
            , kwHzAlpha
            , kwHzS
            , kwHzSd
            , kwHzF
            , kwDpNRatio
            , kwDpSRatio
            , kwDpMode
            , kwDpF
            , kwDpAlpha
            , kwRGap
            , kwResFric
            , kwResMoment
            , kwResS
            , kwResKr
            , kwUserArea
            , kwHzRRMult
        };

        RR_HERTZ_EXPORT ContactModelRRHertz();
        RR_HERTZ_EXPORT virtual ~ContactModelRRHertz();
        virtual void                copy(const ContactModel* c) override;
        virtual void                archive(ArchiveStream&);

        virtual QString  getName() const { return "rr_hertz"; }
        virtual void     setIndex(int i) { index_ = i; }
        virtual int      getIndex() const { return index_; }

        virtual QString  getProperties() const {
            return "hz_shear"
                ",hz_poiss"
                ",fric"
                ",hz_alpha"
                ",hz_slip"
                ",hz_mode"
                ",hz_force"
                ",dp_nratio"
                ",dp_sratio"
                ",dp_mode"
                ",dp_force"
                ",dp_alpha"
                ",rgap"
                ",rr_fric"
                ",rr_moment"
                ",rr_slip"
                ",rr_kr"
                ",user_area";
                
        }

        enum EnergyKeys { kwEStrain = 1, kwERRStrain, kwESlip, kwERRSlip, kwEDashpot };
        virtual QString  getEnergies() const { return "energy-strain,energy-rrstrain,energy-slip,energy-rrslip,energy-dashpot"; }
        virtual double   getEnergy(uint i) const;  // Base 1
        virtual bool     getEnergyAccumulate(uint i) const; // Base 1
        virtual void     setEnergy(uint i, const double& d); // Base 1
        virtual void     activateEnergy() { if (energies_) return; energies_ = NEWC(Energies()); }
        virtual bool     getEnergyActivated() const { return (energies_ != 0); }

        enum FishCallEvents { fActivated = 0, fSlipChange };
        virtual QString  getFishCallEvents() const { return "contact_activated,slip_change"; }
        virtual QVariant getProperty(uint i, const IContact*) const;
        virtual bool     getPropertyGlobal(uint i) const;
        virtual bool     setProperty(uint i, const QVariant& v, IContact*);
        virtual bool     getPropertyReadOnly(uint i) const;

        virtual bool     supportsInheritance(uint i) const;
        virtual bool     getInheritance(uint i) const { assert(i < 32); quint32 mask = to<quint32>(1 << i);  return (inheritanceField_ & mask) ? true : false; }
        virtual void     setInheritance(uint i, bool b) { assert(i < 32); quint32 mask = to<quint32>(1 << i);  if (b) inheritanceField_ |= mask;  else inheritanceField_ &= ~mask; }


        // Enumerator for contact model methods.
        enum MethodKeys { kwDeformability = 1, kwArea };
        // Contact model methoid names in a comma separated list. The order corresponds with
        // the order of the MethodKeys enumerator above.  
        virtual QString  getMethods() const { return "deformability,area"; }
        // Return a comma seprated list of the contact model method arguments (base 1).
        virtual QString  getMethodArguments(uint i) const;
        // Set contact model method arguments (base 1). 
        // The return value denotes whether or not the update has affected the timestep
        // computation (by having modified the translational or rotational tangent stiffnesses).
        // If true is returned, then the timestep will be recomputed.
        //virtual bool     setMethod(uint i, const QVector<QVariant> &vl, IContact *con = 0);



        virtual uint     getMinorVersion() const;

        virtual bool    validate(ContactModelMechanicalState* state, const double& timestep);
        virtual bool    endPropertyUpdated(const QString& name, const IContactMechanical* c);
        virtual bool    forceDisplacementLaw(ContactModelMechanicalState* state, const double& timestep);
        virtual DVect2  getEffectiveTranslationalStiffness() const { return effectiveTranslationalStiffness_; }
        virtual DAVect  getEffectiveRotationalStiffness() const { return effectiveRotationalStiffness_; }

        virtual ContactModelRRHertz* clone() const override { return NEWC(ContactModelRRHertz()); }
        virtual double              getActivityDistance() const { return rgap_; }
        virtual bool                isOKToDelete() const { return !isBonded(); }
        virtual void                resetForcesAndMoments() { hz_F(DVect(0.0)); dp_F(DVect(0.0)); res_M(DAVect(0.0)); if (energies_) {energies_->estrain_ = 0.0;  energies_->errstrain_ = 0.0;  energies_->errstrain_ = 0.0;  } }


        virtual void                setForce(const DVect& v, IContact* c);
        virtual void                setArea(const double&) { throw Exception("The setArea method cannot be used with the Hertz contact model."); }
        virtual double              getArea() const { return 0.0; }

        virtual bool     checkActivity(const double& gap) { return gap <= rgap_; }

        virtual bool     isSliding() const { return hz_slip_; }
        virtual bool     isBonded() const { return false; }
        virtual void     propagateStateInformation(IContactModelMechanical* oldCm, const CAxes& oldSystem = CAxes(), const CAxes& newSystem = CAxes());
        virtual void     setNonForcePropsFrom(IContactModel* oldCM);

        const double& hz_shear() const { return hz_shear_; }
        void           hz_shear(const double& d) { hz_shear_ = d; }
        const double& hz_poiss() const { return hz_poiss_; }
        void           hz_poiss(const double& d) { hz_poiss_ = d; }
        const double& fric() const { return fric_; }
        void           fric(const double& d) { fric_ = d; }
        uint           hz_mode() const { return hz_mode_; }
        void           hz_mode(uint i) { hz_mode_ = i; }
        const double& hz_alpha() const { return hz_alpha_; }
        void           hz_alpha(const double& d) { hz_alpha_ = d; }
        const DVect& hz_F() const { return hz_F_; }
        void           hz_F(const DVect& f) { hz_F_ = f; }
        bool           hz_S() const { return hz_slip_; }
        void           hz_S(bool b) { hz_slip_ = b; }
        const double& hn() const { return hn_; }
        void           hn(const double& d) { hn_ = d; }
        const double& hs() const { return hs_; }
        void           hs(const double& d) { hs_ = d; }
        const double& rgap() const { return rgap_; }
        void           rgap(const double& d) { rgap_ = d; }
        const double& rr_hz_mult() const { return rr_hz_mult_; }
        void		   rr_hz_mult(const double& d) { rr_hz_mult_ = d; }

        bool     hasDamping() const { return dpProps_ ? true : false; }
        double   dp_nratio() const { return (hasDamping() ? (dpProps_->dp_nratio_) : 0.0); }
        void     dp_nratio(const double& d) { if (!hasDamping()) return; dpProps_->dp_nratio_ = d; }
        double   dp_sratio() const { return hasDamping() ? dpProps_->dp_sratio_ : 0.0; }
        void     dp_sratio(const double& d) { if (!hasDamping()) return; dpProps_->dp_sratio_ = d; }
        int      dp_mode() const { return hasDamping() ? dpProps_->dp_mode_ : -1; }
        void     dp_mode(int i) { if (!hasDamping()) return; dpProps_->dp_mode_ = i; }
        DVect    dp_F() const { return hasDamping() ? dpProps_->dp_F_ : DVect(0.0); }
        void     dp_F(const DVect& f) { if (!hasDamping()) return; dpProps_->dp_F_ = f; }
        double   dp_alpha() const { return hasDamping() ? dpProps_->dp_alpha_ : 0.0; }
        void     dp_alpha(const double& d) { if (!hasDamping()) return; dpProps_->dp_alpha_ = d; }

        bool    hasEnergies() const { return energies_ ? true : false; }
        double  estrain() const { return hasEnergies() ? energies_->estrain_ : 0.0; }
        void    estrain(const double& d) { if (!hasEnergies()) return; energies_->estrain_ = d; }
        double  errstrain() const { return hasEnergies() ? energies_->errstrain_ : 0.0; }
        void    errstrain(const double& d) { if (!hasEnergies()) return; energies_->errstrain_ = d; }
        double  eslip() const { return hasEnergies() ? energies_->eslip_ : 0.0; }
        void    eslip(const double& d) { if (!hasEnergies()) return; energies_->eslip_ = d; }
        double  errslip() const { return hasEnergies() ? energies_->errslip_ : 0.0; }
        void    errslip(const double& d) { if (!hasEnergies()) return; energies_->errslip_ = d; }
        double  edashpot() const { return hasEnergies() ? energies_->edashpot_ : 0.0; }
        void    edashpot(const double& d) { if (!hasEnergies()) return; energies_->edashpot_ = d; }

        uint inheritanceField() const { return inheritanceField_; }
        void inheritanceField(uint i) { inheritanceField_ = i; }

        const DVect2& effectiveTranslationalStiffness()  const { return effectiveTranslationalStiffness_; }
        void           effectiveTranslationalStiffness(const DVect2& v) { effectiveTranslationalStiffness_ = v; }
        const DAVect& effectiveRotationalStiffness()  const { return effectiveRotationalStiffness_; }
        void           effectiveRotationalStiffness(const DAVect& v) { effectiveRotationalStiffness_ = v; }

        // Rolling resistance methods
        const double& res_fric() const { return res_fric_; }
        void           res_fric(const double& d) { res_fric_ = d; }
        const DAVect& res_M() const { return res_M_; }
        void           res_M(const DAVect& f) { res_M_ = f; }
        bool           res_S() const { return res_S_; }
        void           res_S(bool b) { res_S_ = b; }
        const double& kr() const { return kr_; }
        void           kr(const double& d) { kr_ = d; }
        const double& fr() const { return fr_; }
        void           fr(const double& d) { fr_ = d; }

        /// Return the total force that the contact model holds.
        virtual DVect    getForce(const IContactMechanical*) const;

        /// Return the total moment on 1 that the contact model holds
        virtual DAVect   getMomentOn1(const IContactMechanical*) const;

        /// Return the total moment on 1 that the contact model holds
        virtual DAVect   getMomentOn2(const IContactMechanical*) const;

    private:
        static int index_;

        bool   updateStiffCoef(const IContactMechanical* con);
        bool   updateEndStiffCoef(const IContactMechanical* con);
        bool   updateEndFric(const IContactMechanical* con);
        void   updateEffectiveStiffness(ContactModelMechanicalState* state);
        bool   updateResFric(const IContactMechanical* con);
        void   setDampCoefficients(const ContactModelMechanicalState& state, double* vcn, double* vcs);
        // inheritance fields
        quint32 inheritanceField_;

        // rr_hertz model
        double      hz_shear_;  // Shear modulus
        double      hz_poiss_;  // Poisson ratio
        double      fric_;      // Coulomb friction coefficient
        double      hz_alpha_;  // Exponent
        bool        hz_slip_;      // the current sliding state
        uint        hz_mode_;     // specifies down-scaling of the shear force when normal unloading occurs 
        DVect       hz_F_;      // Force carried in the rr_hertz model
        double      rgap_;      // Reference gap 

        //viscous model
        struct dpProps {
            dpProps() : dp_nratio_(0.0), dp_sratio_(0.0), dp_mode_(0), dp_F_(DVect(0.0)), dp_alpha_(0.0) {}
            double dp_nratio_;     // normal viscous critical damping ratio
            double dp_sratio_;     // shear  viscous critical damping ratio
            int    dp_mode_;       // for viscous mode (0-4) 0 = dashpots, 1 = tensile limit, 2 = shear limit, 3 = limit both
            DVect  dp_F_;          // Force in the dashpots
            double dp_alpha_;      // exponent
        };
        dpProps* dpProps_;

        // rolling resistance properties
        double res_fric_;       // rolling friction coefficient
        DAVect res_M_;          // moment (bending only)         
        bool   res_S_;          // The current rolling resistance slip state
        double kr_;             // bending rotational stiffness (read-only, calculated internaly) 
        double fr_;             // rolling friction coefficient (rbar*res_fric_) (calculated internaly, not a property) 

        double userArea_;  // Area as specified by the user 

        double rr_hz_mult_;		// Hertz force multiplier to modify the shear stiffness in the rr model

        // energies
        struct Energies {
            Energies() : estrain_(0.0), eslip_(0.0), edashpot_(0.0) {}
            double estrain_;  // elastic energy stored in contact 
            double errstrain_; // elastic energy stored in rolling resistance group
            double eslip_;    // work dissipated by friction 
            double errslip_;   // work dissipated by rolling resistance friction 
            double edashpot_;    // work dissipated by dashpots
        };
        Energies* energies_;

        double      hn_;                           // normal stiffness coefficient
        double      hs_;                           // shear stiffness coefficient
        DVect2  effectiveTranslationalStiffness_;  // effective stiffness
        DAVect  effectiveRotationalStiffness_;      // (Twisting,Bending,Bending) Rotational stiffness (twisting always 0)

    };

} // namespace cmodelsxd
// EoF