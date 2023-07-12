#pragma once
// contactmodelmechanical.h
/** \brief Mechanical contact model class.
    * \file contactmodelmechanical.h
    *
    * \addtogroup contactmodel Mechanical contact model implementation
*/

#include "contactmodel.h"
#include "contactmodel/interface/icontactmodelmechanical.h"

#pragma warning(push)
#pragma warning(disable:4251)

namespace itascaxd
{
    class IContactMechanical;
    class IContactThermal;
}

namespace cmodelsxd
{
    using namespace itasca;
    using namespace itascaxd;

    class ContactModelThermalState;
    /** * \brief 
      * The ContactModelMechnicalState class holds necessary information to communicate back and forth between the code (e.g., <em>PFC</em>) and the contact model.
      * It is derived from ContactModelState, and adds necessary information for mechanical contact models.
      * \ingroup contactmodel
      */
    class ContactModelMechanicalState : public ContactModelState
    {
    public:
        /// Constructor
        ContactModelMechanicalState() : //force_(0.0)
                                      //, momentOn1_(0.0)
                                      //, momentOn2_(0.0)
                                      /*,*/ relativeTranslationalIncrement_(0.0)
                                      , relativeAngularIncrement_(0.0)
                                      , end1Curvature_(0.0)
                                      , end2Curvature_(0.0)
                                      , inertialMass_(0.0)
                                      , gap_(0.0)
                                      , canFail_(true) { }


        /// Destructor
        virtual ~ContactModelMechanicalState() { };
        /// Return a const pointer to the IContactMechanical interface
        virtual const IContactMechanical *getMechanicalContact() const=0;
        /// Return a const pointer to the IContact interface
        virtual const IContact * getContact() const=0;

        //DVect       force_;                            ///< current total force  at this contact (computed by the contact model) 
        //DAVect      momentOn1_;                        ///< moment applied to end1
        //DAVect      momentOn2_;                        ///< moment applied to end2
        DVect       relativeTranslationalIncrement_;   ///< current relative translational displacement increment
        DAVect      relativeAngularIncrement_;         ///< current relative angular displacement increment
        DVect2      end1Curvature_;                    ///< principal curvatures of end1 (min,max)
        DVect2      end2Curvature_;                    ///< principal curvatures of end2 (min,max)  
        double      inertialMass_;                     ///< Effective inertial mass of the contact (required for viscous damping)
        double      gap_;                              ///< current contact gap
        bool        canFail_;                          ///< failure should be discarded
    };

    /** * \brief 
      * Mechanical contact model implementation.
      * \ingroup contactmodel
      */

    class CONTACTMODEL_EXPORT ContactModelMechanical :  public ContactModel
                                                      , public IContactModelMechanical {
    public:
        /// Constructor
        ContactModelMechanical();
        
        /// Destructor
        virtual ~ContactModelMechanical();
        
        /// Prefix for this type of plugin.
        static const char *  getPluginPrefix() { return "contactmodelmechanical"; }
        
        /// Directory for this type of plugin
        static const char *  getPluginDirectory() { return "contactmodels/mechanical"; }

        //  IContactModel overrides

        /// Generic implementation - by default it is always OK to delete a contact.
        virtual bool    isOKToDelete() const { return true; }

        // IContactModelMechanical functions.

        /// Return the IContactModel pointer.
        virtual ContactModel * getContactModel() {return this;}
        
        /// Return the const IContactModel pointer.
        virtual const ContactModel * getContactModel() const {return this;}
        
        /// Default implementation - the contact is not active.
        virtual bool    checkActivity(const double &) {return false;}
        
        /// Default implementation - the contact model is not sliding.
        virtual bool    isSliding() const { return false; }
        
        /// Default implementation - the contact model is not bonded.
        virtual bool    isBonded() const { return false; }

        /// Default implementation - the contact model is not bonded.
        virtual void    unbond() { }

        /// Default implementation - the contact model has no normal.
        virtual bool    hasNormal() const { return false; };
        
        /// Default implementation - the contact model normal is the 0 vector.
        virtual DVect3  getNormal() const { return DVect3(0.0); }
        
        /// Default implementation - state information is not propagated. 
        virtual void    propagateStateInformation(IContactModelMechanical *,const CAxes &n=CAxes(),const CAxes &l=CAxes()) {n; l;}
        
        /// Returns true if the property was actually updated in the contact model. 
        /// Used for inheritance of properties from piece. Must be implemented.
        virtual bool    endPropertyUpdated(const QString &name,const IContactMechanical *c)=0;

        /// Returns true if contact is valid. Must be implemented.
        virtual bool    validate(ContactModelMechanicalState *state,const double &timestep)=0;

        /// Updates force acting on end2 and moments acting on end1 and end2.
        /// Returns true if contact is active. Must be implemented.
        virtual bool    forceDisplacementLaw(ContactModelMechanicalState *state,const double &timestep)=0;

        /// Used for explicit mechanical/thermal coupling. Returns true if anything changed.
        virtual bool    thermalCoupling(ContactModelMechanicalState *,ContactModelThermalState * ,IContactThermal *,const double &) {return false;}

        /// Returns timestep limits (defaults to (0.0,infinity)). 
        /// These are further timestep restrictions that the contact model can place on the simulation, over and above those implied by stiffness.
        virtual DVect2  getTimestepLimits(ContactModelMechanicalState *,const double &) const { return DVect2(0.0,limits<double>::max());}
        
        /// Return the effective translational stiffness - used for timestep calculation.
        virtual DVect2  getEffectiveTranslationalStiffness() const {return DVect2(0.0,0.0);}
        
        /// Return the effective rotational stiffness - used for timestep calculation.
        virtual DAVect  getEffectiveRotationalStiffness() const {return DAVect(0.0);}

        /// Default implementation so that no sphere list must be defined. 
        virtual void    getSphereList(const IContact *con,std::vector<DVect> *pos,std::vector<double> *rad,std::vector<double> *val) { con; pos; rad; val; }
#ifdef THREED

        /// Default implementation so that no disk list must be defined. 
        virtual void    getDiskList(const IContact *con,std::vector<DVect> *pos,std::vector<DVect> *normal,std::vector<double> *radius,std::vector<double> *val) { con; pos; normal; radius; val; }
#endif

        /// Default implementation so that no cylinder list must be defined. 
        virtual void    getCylinderList(const IContact *con,std::vector<DVect> *bot,std::vector<DVect> *top,std::vector<double> *radlow,std::vector<double> *radhi,std::vector<double> *val) { con; bot; top; radlow; radhi; val; }

        /// Return the total force that the contact model holds.
        virtual DVect   getForce(const IContactMechanical *) const { return DVect(0.0); }

        /// Return the total moment on 1 that the contact model holds
        virtual DAVect   getMomentOn1(const IContactMechanical *) const { return DAVect(0.0); }

        /// Return the total moment on 2 that the contact model holds
        virtual DAVect   getMomentOn2(const IContactMechanical *c) const { return getMomentOn1(c); }

        virtual ContactModelMechanical *clone() const { throw Exception("Must be reimplemented."); }

    };
} // namespace cmodelxd

#pragma warning(pop)


// EoF