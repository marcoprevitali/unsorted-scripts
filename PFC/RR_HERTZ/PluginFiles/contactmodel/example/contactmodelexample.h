#pragma once
/** \file contactmodelexample.h
  * \brief Example Mechanical Contact Model Implementation.
  *
  * \defgroup ContactModelExample Example Mechanical Contact Model Implementation
  * \addtogroup ContactModelExample
  * @{
  * \brief 
  * This section describes how to define a new mechanical contact model class that can be loaded as an Itasca DLL plugin.\n
  *
  * The <em>PFC C++ Plugin</em> enables creation of custom contact models, implemented in C++.
  * A good introduction to programming in C++ is provided in <b><em>Teach Yourself C++, 6th Ed</em></b>, by Al Stevens. (Foster City, CA: IDG Books Worldwide, 2000). 
  * What follows assumes that the reader has a working knowledge of the C++ programming language.\n
  *
  * A new class named ContactModelExample, which inherits from the ContactModelMechanical base class, is defined in the cmodelsxd namespace.
  * Pure virtual methods in the base class are implemented, and other virtual methods are overridden to provide the desired behavior.\n
  *
  * Upon compilation, a new DLL is created, that can be loaded into <em>PFC</em> at runtime. Once loaded, the new contact model can be used
  * as any other built-in contact model: it can be registered with the Contact Model Assignment Table, installed at desired contacts,
  * and be queried or modified using the generic PFC contact commands and <em>FISH</em> access.\n
  *
  * \details 
  * The ContactModelExample mechanical contact model consists in a simplified version of the linear contact model available with PFC.
  * Its formulation is similar to that of the linear contact model, and includes:
  *    - a linear normal force, proportional to contact overlap with a constant normal stiffness property <b>kn</b>
  *    - a linear shear force, proportional to accumulated shear displacement with a constant shear stiffness property <b>ks</b>
  *    - a frictional behavior, defined by a constant Coulomb friction coefficient property <b>fric</b>
  *    - a normal dashpot force, proportional to the relative normal velocity at the contact location with a normal dashpot property <b>dp_nratio</b>
  *    - a shear dashpot force, proportional to the relative shear velocity at the contact location with a shear dashpot property <b>dp_sratio</b>
  *    - a control on the activation of the normal and shear dashpots with a dashpot mode switch integer property <b>dp_mode</b>   
  *    - two read-only deformability properties <b>emod</b> and <b>kratio</b>
  *    - a <b>deformability</b> method, which takes two arguments <b>emod</b> and <b>kratio</b>, and allows to set the normal and shear stiffness properties based on desired deformabilty and contact effective radius 
  *    - three energy partitions: <b>estrain</b> (strain energy), <b>eslip</b> (energy dissipated by frictional slip), and <b>edashpot</b> (energy disspiated by the dashpots)
  *    - two FISH callback events: <b>contact_activated</b> that is emitted when the contact first becomes active, and <b>slip_change</b> that is emitted when the slip state changes
  *    - The total linear force (normal + shear contribution shear) is accessible with the <b>lin_f</b> property. 
  *    - The total dashpot force (normal + shear contributions) is accessible with the <b>dp_f</b> property.   
  *    - The name of the model is <b>example</b>
  *
  * This example mechanical contact model differs from the linear contact model available with <em>PFC</em> because it does not provide the possibility
  * to define a reference gap or to use an incremental formulation to calculate the normal component of the linear force.
  *
  */

#include "contactmodel/src/contactmodelmechanical.h"

#ifdef example_LIB
#  define example_EXPORT EXPORT_TAG
#elif defined(NO_MODEL_IMPORT)
#  define example_EXPORT
#else
#  define example_EXPORT IMPORT_TAG
#endif

namespace cmodelsxd {
    using namespace itasca;

    /** * \brief 
        * ContactModelExample class, derived from ContactModelMechanical.
        * \details 
        * A mechanical contact model class must be derived from the ContactModelMechanical base class, and must implement
        * all pure virtual methods in the base class. Other virtual methods have default implementation in the base class,
        * that can be overriden to achieve specific behavior. 
        * \ingroup ContactModelExample
        */
    class ContactModelExample : public ContactModelMechanical {
    public:
        // Constructor: Set default values for contact model properties.
        example_EXPORT ContactModelExample();
        // Destructor, called when contact is deleted: free allocated memory, etc.
        example_EXPORT virtual ~ContactModelExample();
        // Contact model name (used as keyword for commands and FISH).
        virtual QString  getName() const override { return "example"; }
        // The index provides a quick way to determine the type of contact model.
        // Each type of contact model in PFC must have a unique index; this is assigned
        // by PFC when the contact model is loaded. This index should be set to -1
        virtual void     setIndex(int i) override { index_ = i; }
        virtual int      getIndex() const override { return index_; }
        // Contact model version number (e.g., MyModel05_1). The version number can be
        // accessed during the save-restore operation (within the archive method,
        // testing {stream.getRestoreVersion() == getMinorVersion()} to allow for 
        // future modifications to the contact model data structure.
        virtual uint     getMinorVersion() const override;
        // Copy the state information to a newly created contact model.
        // Provide access to state information, for use by copy method.
        virtual void     copy(const ContactModel* c) override;
        // Provide save-restore capability for the state information.
        virtual void     archive(ArchiveStream&) override;
        // Enumerator for the properties.
        enum PropertyKeys {
            kwKn = 1
            , kwKs
            , kwFric
            , kwLinF
            , kwLinS
            , kwLinMode
            , kwRGap
            , kwEmod
            , kwKRatio
            , kwDpNRatio
            , kwDpSRatio
            , kwDpMode
            , kwDpF
            , kwUserArea
        };
        // Contact model property names in a comma separated list. The order corresponds with
        // the order of the PropertyKeys enumerator above. One can visualize any of these 
        // properties in PFC automatically. 
        virtual QString  getProperties() const override {
            return "kn"
                ",ks"
                ",fric"
                ",lin_force"
                ",lin_slip"
                ",lin_mode"
                ",rgap"
                ",emod"
                ",kratio"
                ",dp_nratio"
                ",dp_sratio"
                ",dp_mode"
                ",dp_force"
                ",user_area";
        }
        // Enumerator for the energies.
        enum EnergyKeys {
            kwEStrain = 1
            , kwESlip
            , kwEDashpot
        };
        // Contact model energy names in a comma separated list. The order corresponds with
        // the order of the EnergyKeys enumerator above. 
        virtual QString  getEnergies() const override {
            return "estrain"
                ",eslip"
                ",edashpot";
        }
        // Returns the value of the energy (base 1 - getEnergy(1) returns the estrain energy).
        virtual double   getEnergy(uint i) const override;
        // Returns whether or not each energy is accumulated (base 1 - getEnergyAccumulate(1) 
        // returns wther or not the estrain energy is accumulated which is false).
        virtual bool     getEnergyAccumulate(uint i) const override;
        // Set an energy value (base 1 - setEnergy(1) sets the estrain energy).
        virtual void     setEnergy(uint i, const double& d) override; // Base 1
        // Activate the energy. This is only called if the energy tracking is enabled. 
        virtual void     activateEnergy() override { if (energies_) return; energies_ = NEWC(Energies()); }
        // Returns whether or not the energy tracking has been enabled for this contact.
        virtual bool     getEnergyActivated() const override { return (energies_ != 0); }

        // Enumerator for contact model related FISH callback events. 
        enum FishCallEvents {
            fActivated = 0
            , fSlipChange
        };
        // Contact model FISH callback event names in a comma separated list. The order corresponds with
        // the order of the FishCallEvents enumerator above. 
        virtual QString  getFishCallEvents() const override {
            return
                "contact_activated"
                ",slip_change";
        }

        // Return the specified contact model property.
        virtual QVariant getProperty(uint i, const IContact*) const override;
        // The return value denotes whether or not the property corresponds to the global
        // or local coordinate system (TRUE: global system, FALSE: local system). The
        // local system is the contact-plane system (nst) defined as follows.
        // If a vector V is expressed in the local system as (Vn, Vs, Vt), then V is
        // expressed in the global system as {Vn*nc + Vs*sc + Vt*tc} where where nc, sc
        // and tc are unit vectors in directions of the nst axes.
        // This is used when rendering contact model properties that are vectors.
        virtual bool     getPropertyGlobal(uint i) const override;
        // Set the specified contact model property, ensuring that it is of the correct type
        // and within the correct range --- if not, then throw an exception.
        // The return value denotes whether or not the update has affected the timestep
        // computation (by having modified the translational or rotational tangent stiffnesses).
        // If true is returned, then the timestep will be recomputed.
        virtual bool     setProperty(uint i, const QVariant& v, IContact*) override;
        // The return value denotes whether or not the property is read-only
        // (TRUE: read-only, FALSE: read-write).
        virtual bool     getPropertyReadOnly(uint i) const override;

        // The return value denotes whether or not the property is inheritable
        // (TRUE: inheritable, FALSE: not inheritable). Inheritance is provided by
        // the endPropertyUpdated method.
        virtual bool     supportsInheritance(uint i) const override;
        // Return whether or not inheritance is enabled for the specified property.
        virtual bool     getInheritance(uint i) const override { assert(i < 32); quint32 mask = to<quint32>(1 << i);  return (inheritanceField_ & mask) ? true : false; }
        // Set the inheritance flag for the specified property.
        virtual void     setInheritance(uint i, bool b) override { assert(i < 32); quint32 mask = to<quint32>(1 << i);  if (b) inheritanceField_ |= mask;  else inheritanceField_ &= ~mask; }

        // Enumerator for contact model methods.
        enum MethodKeys { kwDeformability = 1, kwArea };
        // Contact model methoid names in a comma separated list. The order corresponds with
        // the order of the MethodKeys enumerator above.  
        virtual QString  getMethods() const override { return "deformability,area"; }
        // Return a comma seprated list of the contact model method arguments (base 1).
        virtual QString  getMethodArguments(uint i) const override;
        // Set contact model method arguments (base 1). 
        // The return value denotes whether or not the update has affected the timestep
        // computation (by having modified the translational or rotational tangent stiffnesses).
        // If true is returned, then the timestep will be recomputed.
        virtual bool     setMethod(uint i, const QVector<QVariant>& vl, IContact* con = 0) override;

        // Prepare for entry into ForceDispLaw. The validate function is called when:
        // (1) the contact is created, (2) a property of the contact that returns a true via
        // the setProperty method has been modified and (3) when a set of cycles is executed
        // via the {cycle N} command.
        // Return value indicates contact activity (TRUE: active, FALSE: inactive).
        virtual bool    validate(ContactModelMechanicalState* state, const double& timestep) override;
        // The endPropertyUpdated method is called whenever a surface property (with a name
        // that matches an inheritable contact model property name) of one of the contacting
        // pieces is modified. This allows the contact model to update its associated
        // properties. The return value denotes whether or not the update has affected
        // the time step computation (by having modified the translational or rotational
        // tangent stiffnesses). If true is returned, then the time step will be recomputed.  
        virtual bool    endPropertyUpdated(const QString& name, const IContactMechanical* c) override;
        // The forceDisplacementLaw function is called during each cycle. Given the relative
        // motion of the two contacting pieces (via
        //   state->relativeTranslationalIncrement_ (Ddn, Ddss, Ddst)
        //   state->relativeAngularIncrement_       (Dtt, Dtbs, Dtbt)
        //     Ddn  : relative normal-displacement increment, Ddn > 0 is opening
        //     Ddss : relative  shear-displacement increment (s-axis component)
        //     Ddst : relative  shear-displacement increment (t-axis component)
        //     Dtt  : relative twist-rotation increment
        //     Dtbs : relative  bend-rotation increment (s-axis component)
        //     Dtbt : relative  bend-rotation increment (t-axis component)
        //       The relative displacement and rotation increments:
        //         Dd = Ddn*nc + Ddss*sc + Ddst*tc
        //         Dt = Dtt*nc + Dtbs*sc + Dtbt*tc
        //       where nc, sc and tc are unit vectors in direc. of the nst axes, respectively.
        //       [see {Table 1: Contact State Variables} in PFC Model Components:
        //       Contacts and Contact Models: Contact Resolution]
        // ) and the contact properties, this function must update the contact force and
        // moment (via state->force_, state->momentOn1_, state->momentOn2_).
        //   The force_ is acting on piece 2, and is expressed in the local coordinate system
        //   (defined in getPropertyGlobal) such that the first component positive denotes
        //   compression. If we define the moment acting on piece 2 by Mc, and Mc is expressed
        //   in the local coordinate system (defined in getPropertyGlobal), then we must set
        //   {state->momentOn1_ = -Mc}, {state->momentOn2_ = Mc} and call
        //   state->getMechanicalContact()->updateResultingTorquesLocal(...) after having set
        //   force_.
        // The return value indicates the contact activity status (TRUE: active, FALSE:
        // inactive) during the next cycle.
        // Additional information:
        //   * If state->activated() is true, then the contact has just become active (it was
        //     inactive during the previous time step).
        //   * Fully elastic behavior is enforced during the SOLVE ELASTIC command by having
        //     the forceDispLaw handle the case of {state->canFail_ == true}.
        virtual bool    forceDisplacementLaw(ContactModelMechanicalState* state, const double& timestep) override;
        // The getEffectiveXStiffness functions return the translational and rotational
        // tangent stiffnesses used to compute a stable time step. When a contact is sliding,
        // the translational tangent shear stiffness is zero (but this stiffness reduction
        // is typically ignored when computing a stable time step). If the contact model
        // includes a dashpot, then the translational stiffnesses must be increased (see
        // Potyondy (2009)).
        //   [Potyondy, D. “Stiffness Matrix at a Contact Between Two Clumps, ” Itasca
        //   Consulting Group, Inc., Minneapolis, MN, Technical Memorandum ICG6863-L,
        //   December 7, 2009.]
        virtual DVect2  getEffectiveTranslationalStiffness() const override { return effectiveTranslationalStiffness_; }
        virtual DAVect  getEffectiveRotationalStiffness() const override { return DAVect(0.0); }

        // Return a new instance of the contact model. This is used in the CMAT
        // when a new contact is created. 
        virtual ContactModelExample* clone() const override;
        // The getActivityDistance function is called by the contact-resolution logic when
        // the CMAT is modified. Return value is the activity distance used by the
        // checkActivity function. For the hill model, this is zero, because we
        // provide a moisture gap via the proximity of the CMAT followed by CLEAN command.
        virtual double              getActivityDistance() const override { return rgap_; }
        // The isOKToDelete function is called by the contact-resolution logic when...
        // Return value indicates whether or not the contact may be deleted.
        // If TRUE, then the contact may be deleted when it is inactive.
        // If FALSE, then the contact may not be deleted (under any condition).
        virtual bool                isOKToDelete() const override { return !isBonded(); }
        // Zero the forces and moments stored in the contact model. This function is called
        // when the contact becomes inactive.
        virtual void                resetForcesAndMoments() override { lin_F(DVect(0.0)); dp_F(DVect(0.0)); if (energies_) energies_->estrain_ = 0.0; }
        virtual void                setForce(const DVect& v, IContact*) override { lin_F(v); }
        virtual void                setArea(const double& d) override { userArea_ = d; }
        virtual double              getArea() const override { return userArea_; }

        // The checkActivity function is called by the contact-resolution logic when...
        // Return value indicates contact activity (TRUE: active, FALSE: inactive).
        // A contact with the hill model is active if it is wet, or if the contact gap is
        // less than or equal to zero.
        virtual bool     checkActivity(const double& gap) override { return  gap <= rgap_; }

        // Returns the sliding state (FALSE is returned if not implemented).
        virtual bool     isSliding() const override { return lin_S_; }
        // Returns the bonding state (FALSE is returned if not implemented).
        virtual bool     isBonded() const override { return false; }

        // Both of these methods are called only for contacts with facets where the wall 
        // resolution scheme is set the full. In such cases one might wish to propagate 
        // contact state information (e.g., shear force) from one active contact to another. 
        // See the Faceted Wall section in the documentation. 
        virtual void     propagateStateInformation(IContactModelMechanical* oldCm, const CAxes& oldSystem = CAxes(), const CAxes& newSystem = CAxes()) override;
        virtual void     setNonForcePropsFrom(IContactModel* oldCM) override;

        /// Return the total force that the contact model holds.
        virtual DVect    getForce(const IContactMechanical*) const override;

        /// Return the total moment on 1 that the contact model holds
        virtual DAVect   getMomentOn1(const IContactMechanical*) const override;

        /// Return the total moment on 1 that the contact model holds
        virtual DAVect   getMomentOn2(const IContactMechanical*) const override;

        // Methods to get and set properties. 
        const double& kn() const { return kn_; }
        void           kn(const double& d) { kn_ = d; }
        const double& ks() const { return ks_; }
        void           ks(const double& d) { ks_ = d; }
        const double& fric() const { return fric_; }
        void           fric(const double& d) { fric_ = d; }
        const DVect& lin_F() const { return lin_F_; }
        void           lin_F(const DVect& f) { lin_F_ = f; }
        bool           lin_S() const { return lin_S_; }
        void           lin_S(bool b) { lin_S_ = b; }
        uint           lin_mode() const { return lin_mode_; }
        void           lin_mode(uint i) { lin_mode_ = i; }
        const double& rgap() const { return rgap_; }
        void           rgap(const double& d) { rgap_ = d; }

        bool     hasDamping() const { return dpProps_ ? true : false; }
        double   dp_nratio() const { return (hasDamping() ? (dpProps_->dp_nratio_) : 0.0); }
        void     dp_nratio(const double& d) { if (!hasDamping()) return; dpProps_->dp_nratio_ = d; }
        double   dp_sratio() const { return hasDamping() ? dpProps_->dp_sratio_ : 0.0; }
        void     dp_sratio(const double& d) { if (!hasDamping()) return; dpProps_->dp_sratio_ = d; }
        int      dp_mode() const { return hasDamping() ? dpProps_->dp_mode_ : -1; }
        void     dp_mode(int i) { if (!hasDamping()) return; dpProps_->dp_mode_ = i; }
        DVect    dp_F() const { return hasDamping() ? dpProps_->dp_F_ : DVect(0.0); }
        void     dp_F(const DVect& f) { if (!hasDamping()) return; dpProps_->dp_F_ = f; }

        bool    hasEnergies() const { return energies_ ? true : false; }
        double  estrain() const { return hasEnergies() ? energies_->estrain_ : 0.0; }
        void    estrain(const double& d) { if (!hasEnergies()) return; energies_->estrain_ = d; }
        double  eslip() const { return hasEnergies() ? energies_->eslip_ : 0.0; }
        void    eslip(const double& d) { if (!hasEnergies()) return; energies_->eslip_ = d; }
        double  edashpot() const { return hasEnergies() ? energies_->edashpot_ : 0.0; }
        void    edashpot(const double& d) { if (!hasEnergies()) return; energies_->edashpot_ = d; }

        uint inheritanceField() const { return inheritanceField_; }
        void inheritanceField(uint i) { inheritanceField_ = i; }

        const DVect2& effectiveTranslationalStiffness()  const { return effectiveTranslationalStiffness_; }
        void           effectiveTranslationalStiffness(const DVect2& v) { effectiveTranslationalStiffness_ = v; }

    private:
        // Index - used internally by PFC. Should be set to -1 in the cpp file. 
        static int index_;

        // Structure to store the energies. 
        struct Energies {
            Energies() : estrain_(0.0), eslip_(0.0), edashpot_(0.0) {}
            double estrain_;  // elastic energy stored in contact 
            double eslip_;    // work dissipated by friction 
            double edashpot_; // work dissipated by dashpots
        };

        // Structure to store dashpot quantities. 
        struct dpProps {
            dpProps() : dp_nratio_(0.0), dp_sratio_(0.0), dp_mode_(0), dp_F_(DVect(0.0)) {}
            double dp_nratio_;     // normal viscous critical damping ratio
            double dp_sratio_;     // shear  viscous critical damping ratio
            int    dp_mode_;      // for viscous mode (0-4) 0 = dashpots, 1 = tensile limit, 2 = shear limit, 3 = limit both
            DVect  dp_F_;  // Force in the dashpots
        };

        bool   updateKn(const IContactMechanical* con);
        bool   updateKs(const IContactMechanical* con);
        bool   updateFric(const IContactMechanical* con);

        void   updateEffectiveStiffness(ContactModelMechanicalState* state);

        void   setDampCoefficients(const double& mass, double* vcn, double* vcs);

        // Contact model inheritance fields.
        quint32 inheritanceField_;

        // Effective translational stiffness.
        DVect2  effectiveTranslationalStiffness_;

        // linear model properties
        double      kn_;        // Normal stiffness
        double      ks_;        // Shear stiffness
        double      fric_;      // Coulomb friction coefficient
        DVect       lin_F_;     // Force carried in the linear model
        bool        lin_S_;     // The current slip state
        uint        lin_mode_;  // Specifies absolute (0) or incremental (1) calculation mode 
        double      rgap_;      // Reference gap 
        dpProps* dpProps_;   // The viscous properties
        double      userArea_;   // Area as specified by the user                                                                   

        Energies* energies_; // The energies

    };
} // namespace cmodelsxd
  
/// \include contactmodelexample.h
/// @}
// EoF