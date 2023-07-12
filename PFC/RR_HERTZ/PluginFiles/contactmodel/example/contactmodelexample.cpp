/** \file contactmodelexample.cpp
  * \addtogroup ContactModelExample
  * @{
*/
#include "contactmodelexample.h"
#include "contactmodel/src/contactmodelthermal.h"
#include "fish/src/parameter.h"
#include "utility/src/tptr.h"
#include "shared/src/mathutil.h"
#include "version.txt"

#include "kernel/interface/iprogram.h"
#include "module/interface/icontact.h"
#include "module/interface/icontactmechanical.h"
#include "module/interface/icontactthermal.h"
#include "module/interface/ifishcalllist.h"
#include "module/interface/ipiecemechanical.h"
#include "module/interface/ipiece.h"


#ifdef example_LIB
    int __stdcall DllMain(void *,unsigned, void *) {
        return 1;
    }

    extern "C" EXPORT_TAG const char *getName() {
#if DIM==3
        return "contactmodelmechanical3dexample";
#else
        return "contactmodelmechanical2dexample";
#endif
    }

    extern "C" EXPORT_TAG unsigned getMajorVersion() {
        return MAJOR_VERSION;
    }

    extern "C" EXPORT_TAG unsigned getMinorVersion() {
        return UPDATE_VERSION;
    }

    extern "C" EXPORT_TAG void *createInstance() {
        cmodelsxd::ContactModelExample *m = new cmodelsxd::ContactModelExample();
        return (void *)m;
    }
#endif // example_LIB

namespace cmodelsxd {

    static const quint32 linKnMask      = 0x00002; // Base 1!
    static const quint32 linKsMask      = 0x00004;
    static const quint32 linFricMask    = 0x00008;
  
    using namespace itasca;
  
    int ContactModelExample::index_ = -1;

    UInt ContactModelExample::getMinorVersion() const { return UPDATE_VERSION;}

    /// Constructor implementation
    ContactModelExample::ContactModelExample() : inheritanceField_(linKnMask | linKsMask | linFricMask)
        , effectiveTranslationalStiffness_(DVect2(0.0))
        , kn_(0.0)
        , ks_(0.0)
        , fric_(0.0)
        , lin_F_(DVect(0.0))
        , lin_S_(false)
        , lin_mode_(0)
        , rgap_(0.0)
        , dpProps_(0)
        , userArea_(0)
        , energies_(0) {
    }

    ContactModelExample::~ContactModelExample() {
        // Make sure to clean up after yourself!
        if (dpProps_)
            delete dpProps_;
        if (energies_)
            delete energies_;
    }

    void ContactModelExample::archive(ArchiveStream& stream) {
        // The stream allows one to archive the values of the contact model
        // so that it can be saved and restored. The minor version can be
        // used here to allow for incremental changes to the contact model too. 
        stream& kn_;
        stream& ks_;
        stream& fric_;
        stream& lin_F_;
        stream& lin_S_;
        stream& lin_mode_;

        if (stream.getArchiveState() == ArchiveStream::Save) {
            bool b = false;
            if (dpProps_) {
                b = true;
                stream& b;
                stream& dpProps_->dp_nratio_;
                stream& dpProps_->dp_sratio_;
                stream& dpProps_->dp_mode_;
                stream& dpProps_->dp_F_;
            }
            else
                stream& b;

            b = false;
            if (energies_) {
                b = true;
                stream& b;
                stream& energies_->estrain_;
                stream& energies_->eslip_;
                stream& energies_->edashpot_;
            }
            else
                stream& b;
        }
        else {
            bool b(false);
            stream& b;
            if (b) {
                if (!dpProps_)
                    dpProps_ = NEWC(dpProps());
                stream& dpProps_->dp_nratio_;
                stream& dpProps_->dp_sratio_;
                stream& dpProps_->dp_mode_;
                stream& dpProps_->dp_F_;
            }
            stream& b;
            if (b) {
                if (!energies_)
                    energies_ = NEWC(Energies());
                stream& energies_->estrain_;
                stream& energies_->eslip_;
                stream& energies_->edashpot_;
            }
        }

        stream& inheritanceField_;
        stream& effectiveTranslationalStiffness_;

        stream& rgap_;
        stream& userArea_;
    }

    ContactModelExample* ContactModelExample::clone() const
    {
        return NEWC(ContactModelExample()); 
    }

    void ContactModelExample::copy(const ContactModel* cm) {
        // Copy all of the contact model properties. Used in the CMAT 
        // when a new contact is created. 
        ContactModelMechanical::copy(cm);
        const ContactModelExample* in = dynamic_cast<const ContactModelExample*>(cm);
        if (!in) throw std::runtime_error("Internal error: contact model dynamic cast failed.");
        kn(in->kn());
        ks(in->ks());
        fric(in->fric());
        lin_F(in->lin_F());
        lin_S(in->lin_S());
        lin_mode(in->lin_mode());
        rgap(in->rgap());
        if (in->hasDamping()) {
            if (!dpProps_)
                dpProps_ = NEWC(dpProps());
            dp_nratio(in->dp_nratio());
            dp_sratio(in->dp_sratio());
            dp_mode(in->dp_mode());
            dp_F(in->dp_F());
        }
        if (in->hasEnergies()) {
            if (!energies_)
                energies_ = NEWC(Energies());
            estrain(in->estrain());
            eslip(in->eslip());
            edashpot(in->edashpot());
        }
        userArea_ = in->userArea_;
        inheritanceField(in->inheritanceField());
        effectiveTranslationalStiffness(in->effectiveTranslationalStiffness());
    }


    QVariant ContactModelExample::getProperty(uint i, const IContact* con) const {
        // Return the property. The IContact pointer is provided so that 
        // more complicated properties, depending on contact characteristics,
        // can be calcualted. 
        QVariant var;
        switch (i) {
        case kwKn:        return kn_;
        case kwKs:        return ks_;
        case kwFric:      return fric_;
        case kwLinF: {var.setValue(lin_F_); return var; }
        case kwLinS:      return lin_S_;
        case kwLinMode:   return lin_mode_;
        case kwRGap:      return rgap_;
        case kwEmod: {
            const IContactMechanical* c(convert_getcast<IContactMechanical>(con));
            if (c == nullptr) return 0.0;
            double rsq(std::max(c->getEnd1Curvature().y(), c->getEnd2Curvature().y()));
            double rsum(0.0);
            if (c->getEnd1Curvature().y())
                rsum += 1.0 / c->getEnd1Curvature().y();
            if (c->getEnd2Curvature().y())
                rsum += 1.0 / c->getEnd2Curvature().y();
            if (userArea_) {
#ifdef THREED
                rsq = std::sqrt(userArea_ / dPi);
#else
                rsq = userArea_ / 2.0;
#endif        
                rsum = rsq + rsq;
                rsq = 1. / rsq;
            }
#ifdef TWOD               
            return (kn_ * rsum * rsq / 2.0);
#else                     
            return (kn_ * rsum * rsq * rsq) / dPi;
#endif                    
        }
        case kwKRatio:    return (ks_ == 0.0) ? 0.0 : (kn_ / ks_);
        case kwDpNRatio:  return dpProps_ ? dpProps_->dp_nratio_ : 0;
        case kwDpSRatio:  return dpProps_ ? dpProps_->dp_sratio_ : 0;
        case kwDpMode:    return dpProps_ ? dpProps_->dp_mode_ : 0;
        case kwDpF: {
            dpProps_ ? var.setValue(dpProps_->dp_F_) : var.setValue(DVect(0.0));
            return var;
        }
        case kwUserArea:    return userArea_;
        }
        assert(0);
        return QVariant();
    }

    bool ContactModelExample::getPropertyGlobal(uint i) const {
        // Returns whether or not a property is held in the global axis system (TRUE)
        // or the local system (FALSE). Used by the plotting logic.
        switch (i) {
        case kwLinF:
        case kwDpF:
            return false;
        }
        return true;
    }

    bool ContactModelExample::setProperty(uint i, const QVariant& v, IContact*) {
        // Set a contact model property. Return value indicates that the timestep
        // should be recalculated. 
        dpProps dp;
        switch (i) {
        case kwKn: {
            if (!v.canConvert<double>())
                throw Exception("kn must be a double.");
            double val(v.toDouble());
            if (val < 0.0)
                throw Exception("Negative kn not allowed.");
            kn_ = val;
            return true;
        }
        case kwKs: {
            if (!v.canConvert<double>())
                throw Exception("ks must be a double.");
            double val(v.toDouble());
            if (val < 0.0)
                throw Exception("Negative ks not allowed.");
            ks_ = val;
            return true;
        }
        case kwFric: {
            if (!v.canConvert<double>())
                throw Exception("fric must be a double.");
            double val(v.toDouble());
            if (val < 0.0)
                throw Exception("Negative fric not allowed.");
            fric_ = val;
            return false;
        }
        case kwLinF: {
            if (!v.canConvert<DVect>())
                throw Exception("lin_force must be a vector.");
            DVect val(v.value<DVect>());
            lin_F_ = val;
            return false;
        }
        case kwLinMode: {
            if (!v.canConvert<uint>())
                throw Exception("lin_mode must be 0 (absolute) or 1 (incremental).");
            uint val(v.toUInt());
            if (val > 1)
                throw Exception("lin_mode must be 0 (absolute) or 1 (incremental).");
            lin_mode_ = val;
            return false;
        }
        case kwRGap: {
            if (!v.canConvert<double>())
                throw Exception("Reference gap must be a double.");
            double val(v.toDouble());
            rgap_ = val;
            return false;
        }
        case kwDpNRatio: {
            if (!v.canConvert<double>())
                throw Exception("dp_nratio must be a double.");
            double val(v.toDouble());
            if (val < 0.0)
                throw Exception("Negative dp_nratio not allowed.");
            if (val == 0.0 && !dpProps_)
                return false;
            if (!dpProps_)
                dpProps_ = NEWC(dpProps());
            dpProps_->dp_nratio_ = val;
            return true;
        }
        case kwDpSRatio: {
            if (!v.canConvert<double>())
                throw Exception("dp_sratio must be a double.");
            double val(v.toDouble());
            if (val < 0.0)
                throw Exception("Negative dp_sratio not allowed.");
            if (val == 0.0 && !dpProps_)
                return false;
            if (!dpProps_)
                dpProps_ = NEWC(dpProps());
            dpProps_->dp_sratio_ = val;
            return true;
        }
        case kwDpMode: {
            if (!v.canConvert<int>())
                throw Exception("The viscous mode dp_mode must be 0, 1, 2, or 3.");
            int val(v.toInt());
            if (val == 0 && !dpProps_)
                return false;
            if (val < 0 || val > 3)
                throw Exception("The viscous mode dp_mode must be 0, 1, 2, or 3.");
            if (!dpProps_)
                dpProps_ = NEWC(dpProps());
            dpProps_->dp_mode_ = val;
            return false;
        }
        case kwDpF: {
            if (!v.canConvert<DVect>())
                throw Exception("dp_force must be a vector.");
            DVect val(v.value<DVect>());
            if (val.fsum() == 0.0 && !dpProps_)
                return false;
            if (!dpProps_)
                dpProps_ = NEWC(dpProps());
            dpProps_->dp_F_ = val;
            return false;
        }
        case kwUserArea: {
            if (!v.canConvert<double>())
                throw Exception("user_area must be a double.");
            double val(v.toDouble());
            if (val < 0.0)
                throw Exception("Negative user_area not allowed.");
            userArea_ = val;
            return true;
        }
        }
        return false;
    }

    bool ContactModelExample::getPropertyReadOnly(uint i) const {
        // Returns TRUE if a property is read only or FALSE otherwise. 
        switch (i) {
        case kwDpF:
        case kwLinS:
        case kwEmod:
        case kwKRatio:
            return true;
        default:
            break;
        }
        return false;
    }

    bool ContactModelExample::supportsInheritance(uint i) const {
        // Returns TRUE if a property supports inheritance or FALSE otherwise. 
        switch (i) {
        case kwKn:
        case kwKs:
        case kwFric:
            return true;
        default:
            break;
        }
        return false;
    }

    QString  ContactModelExample::getMethodArguments(uint i) const {
        // Return a list of contact model method argument names. 
        switch (i) {
        case kwDeformability:
            return "emod,kratio";
        }
        assert(0);
        return QString();
    }

    bool ContactModelExample::setMethod(uint i, const QVector<QVariant>& vl, IContact* con) {
        // Apply the specified method. 
        IContactMechanical* c(convert_getcast<IContactMechanical>(con));
        switch (i) {
        case kwDeformability: {
            double emod;
            double krat;
            if (vl.at(0).isNull())
                throw Exception("Argument emod must be specified with method deformability in contact model %1.", getName());
            emod = vl.at(0).toDouble();
            if (emod < 0.0)
                throw Exception("Negative emod not allowed in contact model %1.", getName());
            if (vl.at(1).isNull())
                throw Exception("Argument kratio must be specified with method deformability in contact model %1.", getName());
            krat = vl.at(1).toDouble();
            if (krat < 0.0)
                throw Exception("Negative stiffness ratio not allowed in contact model %1.", getName());
            double rsq(std::max(c->getEnd1Curvature().y(), c->getEnd2Curvature().y()));
            double rsum(0.0);
            if (c->getEnd1Curvature().y())
                rsum += 1.0 / c->getEnd1Curvature().y();
            if (c->getEnd2Curvature().y())
                rsum += 1.0 / c->getEnd2Curvature().y();
            if (userArea_) {
#ifdef THREED
                rsq = std::sqrt(userArea_ / dPi);
#else
                rsq = userArea_ / 2.0;
#endif        
                rsum = rsq + rsq;
                rsq = 1. / rsq;
            }
#ifdef TWOD
            kn_ = 2.0 * emod / (rsq * rsum);
#else
            kn_ = dPi * emod / (rsq * rsq * rsum);
#endif
            ks_ = (krat == 0.0) ? 0.0 : kn_ / krat;
            setInheritance(1, false);
            setInheritance(2, false);
            return true;
        }
        case kwArea: {
            if (!userArea_) {
                double rsq(1. / std::max(c->getEnd1Curvature().y(), c->getEnd2Curvature().y()));
#ifdef THREED
                userArea_ = rsq * rsq * dPi;
#else
                userArea_ = rsq * 2.0;
#endif                            
            }
            return true;
        }
        }
        return false;
    }

    double ContactModelExample::getEnergy(uint i) const {
        // Return an energy value. 
        double ret(0.0);
        if (!energies_)
            return ret;
        switch (i) {
        case kwEStrain:  return energies_->estrain_;
        case kwESlip:    return energies_->eslip_;
        case kwEDashpot: return energies_->edashpot_;
        }
        assert(0);
        return ret;
    }

    bool ContactModelExample::getEnergyAccumulate(uint i) const {
        // Returns TRUE if the corresponding energy is accumulated or FALSE otherwise.
        switch (i) {
        case kwEStrain:  return false;
        case kwESlip:    return true;
        case kwEDashpot:    return true;
        }
        assert(0);
        return false;
    }

    void ContactModelExample::setEnergy(uint i, const double& d) {
        // Set an energy value. 
        if (!energies_) return;
        switch (i) {
        case kwEStrain:  energies_->estrain_ = d; return;
        case kwESlip:    energies_->eslip_ = d; return;
        case kwEDashpot: energies_->edashpot_ = d; return;
        }
        assert(0);
        return;
    }

    bool ContactModelExample::validate(ContactModelMechanicalState* state, const double&) {
        // Validate the / Prepare for entry into ForceDispLaw. The validate function is called when:
        // (1) the contact is created, (2) a property of the contact that returns a true via
        // the setProperty method has been modified and (3) when a set of cycles is executed
        // via the {cycle N} command.
        // Return value indicates contact activity (TRUE: active, FALSE: inactive).
        assert(state);
        const IContactMechanical* c = state->getMechanicalContact();
        assert(c);

        if (state->trackEnergy_)
            activateEnergy();

        if (inheritanceField_ & linKnMask)
            updateKn(c);
        if (inheritanceField_ & linKsMask)
            updateKs(c);
        if (inheritanceField_ & linFricMask)
            updateFric(c);

        updateEffectiveStiffness(state);
        return checkActivity(state->gap_);
    }

    static const QString knstr("kn");
    bool ContactModelExample::updateKn(const IContactMechanical* con) {
        assert(con);
        QVariant v1 = con->getEnd1()->getProperty(knstr);
        QVariant v2 = con->getEnd2()->getProperty(knstr);
        if (!v1.isValid() || !v2.isValid())
            return false;
        double kn1 = v1.toDouble();
        double kn2 = v2.toDouble();
        double val = kn_;
        if (kn1 && kn2)
            kn_ = kn1 * kn2 / (kn1 + kn2);
        else if (kn1)
            kn_ = kn1;
        else if (kn2)
            kn_ = kn2;
        return ((kn_ != val));
    }

    static const QString ksstr("ks");
    bool ContactModelExample::updateKs(const IContactMechanical* con) {
        assert(con);
        QVariant v1 = con->getEnd1()->getProperty(ksstr);
        QVariant v2 = con->getEnd2()->getProperty(ksstr);
        if (!v1.isValid() || !v2.isValid())
            return false;
        double ks1 = v1.toDouble();
        double ks2 = v2.toDouble();
        double val = ks_;
        if (ks1 && ks2)
            ks_ = ks1 * ks2 / (ks1 + ks2);
        else if (ks1)
            ks_ = ks1;
        else if (ks2)
            ks_ = ks2;
        return ((ks_ != val));
    }

    static const QString fricstr("fric");
    bool ContactModelExample::updateFric(const IContactMechanical* con) {
        assert(con);
        QVariant v1 = con->getEnd1()->getProperty(fricstr);
        QVariant v2 = con->getEnd2()->getProperty(fricstr);
        if (!v1.isValid() || !v2.isValid())
            return false;
        double fric1 = std::max(0.0, v1.toDouble());
        double fric2 = std::max(0.0, v2.toDouble());
        double val = fric_;
        fric_ = std::min(fric1, fric2);
        return ((fric_ != val));
    }

    bool ContactModelExample::endPropertyUpdated(const QString& name, const IContactMechanical* c) {
        // The endPropertyUpdated method is called whenever a surface property (with a name
        // that matches an inheritable contact model property name) of one of the contacting
        // pieces is modified. This allows the contact model to update its associated
        // properties. The return value denotes whether or not the update has affected
        // the time step computation (by having modified the translational or rotational
        // tangent stiffnesses). If true is returned, then the time step will be recomputed.  
        assert(c);
        QStringList availableProperties = getProperties().simplified().replace(" ", "").split(",", QString::SkipEmptyParts);
        QRegExp rx(name, Qt::CaseInsensitive);
        int idx = availableProperties.indexOf(rx) + 1;
        bool ret = false;

        if (idx <= 0)
            return ret;

        switch (idx) {
        case kwKn: { //kn
            if (inheritanceField_ & linKnMask)
                ret = updateKn(c);
            break;
        }
        case kwKs: { //ks
            if (inheritanceField_ & linKsMask)
                ret = updateKs(c);
            break;
        }
        case kwFric: { //fric
            if (inheritanceField_ & linFricMask)
                updateFric(c);
            break;
        }
        }
        return ret;
    }

    void ContactModelExample::updateEffectiveStiffness(ContactModelMechanicalState*) {
        DVect2 ret(kn_, ks_);
        // correction if viscous damping active
        if (dpProps_) {
            DVect2 correct(1.0);
            if (dpProps_->dp_nratio_)
                correct.rx() = sqrt(1.0 + dpProps_->dp_nratio_ * dpProps_->dp_nratio_) - dpProps_->dp_nratio_;
            if (dpProps_->dp_sratio_)
                correct.ry() = sqrt(1.0 + dpProps_->dp_sratio_ * dpProps_->dp_sratio_) - dpProps_->dp_sratio_;
            ret /= (correct * correct);
        }
        effectiveTranslationalStiffness_ = ret;
    }

    bool ContactModelExample::forceDisplacementLaw(ContactModelMechanicalState* state, const double& timestep) {
        assert(state);

        // Current overlap
        double overlap = rgap_ - state->gap_;
        // Relative translational increment
        DVect trans = state->relativeTranslationalIncrement_;
        // Correction factor to account for when the contact becomes newly active.
        // We estimate the time of activity during the timestep when the contact has first 
        // become active and scale the forces accordingly.
        double correction = 1.0;

        // The contact was just activated from an inactive state
        if (state->activated()) {
            // Trigger the FISH callback if one is hooked up to the 
            // contact_activated event.
            if (cmEvents_[fActivated] >= 0) {
                // An std::vector of FISH parameters is returned and these will be passed
                // to the FISH function as an array of FISH symbols as the second
                // argument to the FISH callback function. 
                auto c = state->getContact();
                std::vector<fish::Parameter> arg = { fish::Parameter(c->getIThing()) };
                IFishCallList* fi = const_cast<IFishCallList*>(state->getProgram()->findInterface<IFishCallList>());
                fi->setCMFishCallArguments(c, arg, cmEvents_[fActivated]);

            }
            // Calculate the correction factor.
            if (trans.x()) {
                correction = -1.0 * overlap / trans.x();
                if (correction < 0)
                    correction = 1.0;
            }
        }

        // Angular dispacement increment.
        DAVect ang = state->relativeAngularIncrement_;
        DVect lin_F_old = lin_F_;

        if (lin_mode_ == 0)
            lin_F_.rx() = overlap * kn_; // incremental mode for normal force calculation
        else
            lin_F_.rx() -= correction * trans.x() * kn_; // absolute mode for normal force calculation

          // Normal force can only be positive.
        lin_F_.rx() = std::max(0.0, lin_F_.x());

        // Calculate the shear force.
        DVect sforce(0.0);
        // dim holds the dimension (e.g., 2 for 2D and 3 for 3D)
        // Loop over the shear components (note: the 0 component is the normal component)
        // and calculate the shear force.
        for (int i = 1; i < dim; ++i)
            sforce.rdof(i) = lin_F_.dof(i) - trans.dof(i) * ks_ * correction;

        // The canFail flag corresponds to whether or not the contact can undergo non-linear
        // force-displacement response. If the SOLVE ELASTIC command is given then the 
        // canFail state is set to FALSE. Otherwise it is always TRUE. 
        if (state->canFail_) {
            // Resolve sliding. This is the normal force multiplied by the coefficient of friction.
            double crit = lin_F_.x() * fric_;
            // The is the magnitude of the shear force.
            double sfmag = sforce.mag();
            // Sliding occurs when the magnitude of the shear force is greater than the 
            // critical value.
            if (sfmag > crit) {
                // Lower the shear force to the critical value for sliding.
                double rat = crit / sfmag;
                sforce *= rat;
                // Handle the slip_change event if one has been hooked up. Sliding has commenced.  
                if (!lin_S_ && cmEvents_[fSlipChange] >= 0) {
                    auto c = state->getContact();
                    std::vector<fish::Parameter> arg = { fish::Parameter(c->getIThing()),
                                                         fish::Parameter() };
                    IFishCallList* fi = const_cast<IFishCallList*>(state->getProgram()->findInterface<IFishCallList>());
                    fi->setCMFishCallArguments(c, arg, cmEvents_[fSlipChange]);
                }
                lin_S_ = true;
            }
            else {
                // Handle the slip_change event if one has been hooked up and
                // the contact was previously sliding. Sliding has ceased.  
                if (lin_S_) {
                    if (cmEvents_[fSlipChange] >= 0) {
                        auto c = state->getContact();
                        std::vector<fish::Parameter> arg = { fish::Parameter(c->getIThing()),
                                                             fish::Parameter((qint64)1) };
                        IFishCallList* fi = const_cast<IFishCallList*>(state->getProgram()->findInterface<IFishCallList>());
                        fi->setCMFishCallArguments(c, arg, cmEvents_[fSlipChange]);
                    }
                    lin_S_ = false;
                }
            }
        }

        // Set the shear components of the total force.
        for (int i = 1; i < dim; ++i)
            lin_F_.rdof(i) = sforce.dof(i);

        // Account for dashpot forces if the dashpot structure has been defined. 
        if (dpProps_) {
            dpProps_->dp_F_.fill(0.0);
            double vcn(0.0), vcs(0.0);
            // Calculate the damping coefficients. 
            setDampCoefficients(state->inertialMass_, &vcn, &vcs);
            // First damp the shear components
            for (int i = 1; i < dim; ++i)
                dpProps_->dp_F_.rdof(i) = trans.dof(i) * (-1.0 * vcs) / timestep;
            // Damp the normal component
            dpProps_->dp_F_.rx() -= trans.x() * vcn / timestep;
            // Need to change behavior based on the dp_mode.
            if ((dpProps_->dp_mode_ == 1 || dpProps_->dp_mode_ == 3)) {
                // Limit in tension if not bonded.
                if (dpProps_->dp_F_.x() + lin_F_.x() < 0)
                    dpProps_->dp_F_.rx() = -lin_F_.rx();
            }
            if (lin_S_ && dpProps_->dp_mode_ > 1) {
                // Limit in shear if not sliding.
                double dfn = dpProps_->dp_F_.rx();
                dpProps_->dp_F_.fill(0.0);
                dpProps_->dp_F_.rx() = dfn;
            }
        }

        //Compute energies if energy tracking has been enabled. 
        if (state->trackEnergy_) {
            assert(energies_);
            energies_->estrain_ = 0.0;
            if (kn_)
                // Calcualte the strain energy. 
                energies_->estrain_ = 0.5 * lin_F_.x() * lin_F_.x() / kn_;
            if (ks_) {
                DVect s = lin_F_;
                s.rx() = 0.0;
                double smag2 = s.mag2();
                // Add the shear component of the strain energy.
                energies_->estrain_ += 0.5 * smag2 / ks_;

                if (lin_S_) {
                    // If sliding calculate the slip energy and accumulate it.
                    lin_F_old.rx() = 0.0;
                    DVect avg_F_s = (s + lin_F_old) * 0.5;
                    DVect u_s_el = (s - lin_F_old) / ks_;
                    DVect u_s(0.0);
                    for (int i = 1; i < dim; ++i)
                        u_s.rdof(i) = trans.dof(i);
                    energies_->eslip_ -= std::min(0.0, (avg_F_s | (u_s + u_s_el)));
                }
            }
            if (dpProps_) {
                // Calculate damping energy (accumulated) if the dashpots are active. 
                energies_->edashpot_ -= dpProps_->dp_F_ | trans;
            }
        }

        // This is just a sanity check to ensure, in debug mode, that the force isn't wonky. 
        assert(lin_F_ == lin_F_);
        return true;
    }

    void ContactModelExample::propagateStateInformation(IContactModelMechanical* old, const CAxes& oldSystem, const CAxes& newSystem) {
        // Only called for contacts with wall facets when the wall resolution scheme
        // is set to full!
        // Only do something if the contact model is of the same type
        if (old->getContactModel()->getName().compare("example", Qt::CaseInsensitive) == 0 && !isBonded()) {
            ContactModelExample* oldCm = (ContactModelExample*)old;
#ifdef THREED
            // Need to rotate just the shear component from oldSystem to newSystem

            // Step 1 - rotate oldSystem so that the normal is the same as the normal of newSystem
            DVect axis = oldSystem.e1() & newSystem.e1();
            double c, ang, s;
            DVect re2;
            if (!checktol(axis.abs().maxComp(), 0.0, 1.0, 1000)) {
                axis = axis.unit();
                c = oldSystem.e1() | newSystem.e1();
                if (c > 0)
                    c = std::min(c, 1.0);
                else
                    c = std::max(c, -1.0);
                ang = acos(c);
                s = sin(ang);
                double t = 1. - c;
                DMatrix<3, 3> rm;
                rm.get(0, 0) = t * axis.x() * axis.x() + c;
                rm.get(0, 1) = t * axis.x() * axis.y() - axis.z() * s;
                rm.get(0, 2) = t * axis.x() * axis.z() + axis.y() * s;
                rm.get(1, 0) = t * axis.x() * axis.y() + axis.z() * s;
                rm.get(1, 1) = t * axis.y() * axis.y() + c;
                rm.get(1, 2) = t * axis.y() * axis.z() - axis.x() * s;
                rm.get(2, 0) = t * axis.x() * axis.z() - axis.y() * s;
                rm.get(2, 1) = t * axis.y() * axis.z() + axis.x() * s;
                rm.get(2, 2) = t * axis.z() * axis.z() + c;
                re2 = rm * oldSystem.e2();
            }
            else
                re2 = oldSystem.e2();
            // Step 2 - get the angle between the oldSystem rotated shear and newSystem shear
            axis = re2 & newSystem.e2();
            DVect2 tpf;
            DMatrix<2, 2> m;
            if (!checktol(axis.abs().maxComp(), 0.0, 1.0, 1000)) {
                axis = axis.unit();
                c = re2 | newSystem.e2();
                if (c > 0)
                    c = std::min(c, 1.0);
                else
                    c = std::max(c, -1.0);
                ang = acos(c);
                if (!checktol(axis.x(), newSystem.e1().x(), 1.0, 100))
                    ang *= -1;
                s = sin(ang);
                m.get(0, 0) = c;
                m.get(1, 0) = s;
                m.get(0, 1) = -m.get(1, 0);
                m.get(1, 1) = m.get(0, 0);
                tpf = m * DVect2(oldCm->lin_F_.y(), oldCm->lin_F_.z());
            }
            else {
                m.get(0, 0) = 1.;
                m.get(0, 1) = 0.;
                m.get(1, 0) = 0.;
                m.get(1, 1) = 1.;
                tpf = DVect2(oldCm->lin_F_.y(), oldCm->lin_F_.z());
            }
            DVect pforce = DVect(0, tpf.x(), tpf.y());
#else
            oldSystem;
            newSystem;
            DVect pforce = DVect(0, oldCm->lin_F_.y());
#endif
            for (int i = 1; i < dim; ++i)
                lin_F_.rdof(i) += pforce.dof(i);
            oldCm->lin_F_ = DVect(0.0);
            if (dpProps_ && oldCm->dpProps_) {
#ifdef THREED
                tpf = m * DVect2(oldCm->dpProps_->dp_F_.y(), oldCm->dpProps_->dp_F_.z());
                pforce = DVect(oldCm->dpProps_->dp_F_.x(), tpf.x(), tpf.y());
#else
                pforce = oldCm->dpProps_->dp_F_;
#endif
                dpProps_->dp_F_ += pforce;
                oldCm->dpProps_->dp_F_ = DVect(0.0);
            }
            if (oldCm->getEnergyActivated()) {
                activateEnergy();
                energies_->estrain_ = oldCm->energies_->estrain_;
                energies_->edashpot_ = oldCm->energies_->edashpot_;
                energies_->eslip_ = oldCm->energies_->eslip_;
                oldCm->energies_->estrain_ = 0.0;
                oldCm->energies_->edashpot_ = 0.0;
                oldCm->energies_->eslip_ = 0.0;
            }
            rgap_ = oldCm->rgap_;
        }
        assert(lin_F_ == lin_F_);
    }

    void ContactModelExample::setNonForcePropsFrom(IContactModel* old) {
        // Only called for contacts with wall facets when the wall resolution scheme
        // is set to full!
        // Only do something if the contact model is of the same type
        if (old->getName().compare("example", Qt::CaseInsensitive) == 0 && !isBonded()) {
            ContactModelExample* oldCm = (ContactModelExample*)old;
            kn_ = oldCm->kn_;
            ks_ = oldCm->ks_;
            fric_ = oldCm->fric_;
            lin_mode_ = oldCm->lin_mode_;
            rgap_ = oldCm->rgap_;
            userArea_ = oldCm->userArea_;
            if (oldCm->dpProps_) {
                if (!dpProps_)
                    dpProps_ = NEWC(dpProps());
                dpProps_->dp_nratio_ = oldCm->dpProps_->dp_nratio_;
                dpProps_->dp_sratio_ = oldCm->dpProps_->dp_sratio_;
                dpProps_->dp_mode_ = oldCm->dpProps_->dp_mode_;
            }
        }
    }

    DVect ContactModelExample::getForce(const IContactMechanical*) const {
        DVect ret(lin_F_);
        if (dpProps_)
            ret += dpProps_->dp_F_;
        return ret;
    }

    DAVect ContactModelExample::getMomentOn1(const IContactMechanical* c) const {
        DVect force = getForce(c);
        DAVect ret(0.0);
        c->updateResultingTorqueOn1Local(force, &ret);
        return ret;
    }

    DAVect ContactModelExample::getMomentOn2(const IContactMechanical* c) const {
        DVect force = getForce(c);
        DAVect ret(0.0);
        c->updateResultingTorqueOn2Local(force, &ret);
        return ret;
    }

    void ContactModelExample::setDampCoefficients(const double& mass, double* vcn, double* vcs) {
        *vcn = dpProps_->dp_nratio_ * 2.0 * sqrt(mass * (kn_));
        *vcs = dpProps_->dp_sratio_ * 2.0 * sqrt(mass * (ks_));
    }

} // namespace cmodelsxd
/// @}
// EoF