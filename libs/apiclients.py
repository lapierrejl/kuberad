from datetime import datetime
from kubernetes import client, config
from typing import Sequence


config.load_kube_config()

class FakeEventTime:
    def __get__(self, obj, objtype=None):
        return obj._event_time

    def __set__(self, obj, value):
        obj._event_time = value
        
class FakeEndpoints:
    def __get__(self, obj, objtype=None):
        return obj._endpoints
    def __set__(self, obj, value):
        obj._endpoints = value

def get_kube_contexts(current: bool = False):
    contexts, current_context = config.list_kube_config_contexts()
    if current:
        context_names = [current_context['name']]
    else:
        context_names = [context['name'] for context in contexts]
    
    return context_names
    

class K8sApiClient:
    def __init__(self, apiclient, 
                 removed_apis: Sequence[str], 
                 required_api: str,
                 excluded_manifest_names=[],
                 context=""):
        
        client.EventsV1Event.event_time = FakeEventTime()
        client.V1EndpointSlice.endpoints = FakeEndpoints()
        if context:
            self.context = context
            self.client = apiclient(api_client=config.new_client_from_config(context=self.context))
        else:
            self.client = apiclient()

        self.removed_apis = removed_apis
        self.required_api = required_api
        self.excluded_manifest_names = excluded_manifest_names

    
    def _is_api_removed(self, manifest: dict, type: str):
        k8s_object = {}
        removed_apis = []
        removed_apis_filtered = []
        if manifest.metadata.managed_fields:
            for managed_field in manifest.metadata.managed_fields:
                if managed_field.api_version in self.removed_apis:
                    removed_apis.append(
                        {
                            'api_version': managed_field.api_version,
                            'manager': managed_field.manager,
                            'time': managed_field.time
                        }
                    )
                
            if removed_apis:
                for removed_api in removed_apis:

                    removed_api_time = removed_api['time']
                    oldest_time = removed_api_time

                    for managed_field in manifest.metadata.managed_fields:
                        if managed_field.manager == removed_api['manager']:
                            if managed_field.time > oldest_time:
                                oldest_time = managed_field.time

                    if oldest_time == removed_api_time:
                        removed_apis_filtered.append(removed_api)
                            
                if removed_apis_filtered and manifest.metadata.name not in self.excluded_manifest_names:
                    managed_fields = [{'manager': field.manager, 'api_version': field.api_version, 'time': field.time} for field in manifest.metadata.managed_fields]
                    k8s_object = {
                        'type': type,
                        'name': manifest.metadata.name,
                        'labels': manifest.metadata.labels if manifest.metadata.labels else 'None',
                        'removed_api_references': removed_apis_filtered,
                        'required_api': self.required_api,
                        'managed_fields': managed_fields                    
                    }
        
        return k8s_object

                
    def _find_all_removed_apis(self, manifests, type: str, context=""):
        objects_with_removed_apis = []
        for manifest in manifests:
                removed_apis = self._is_api_removed(manifest, type)
                if removed_apis:
                   objects_with_removed_apis.append(removed_apis)

        return objects_with_removed_apis 


class Admission(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.AdmissionregistrationV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         context,
                         excluded_manifest_names
                         )

    def find_removed_apis_mutatating_web_hooks(self):
        resp = self.client.list_mutating_webhook_configuration(watch=False)
        return self._find_all_removed_apis(resp.items, type='mutating_web_hook')

    def find_removed_apis_validating_web_hooks(self):
        resp = self.client.list_validating_webhook_configuration(watch=False)
        return self._find_all_removed_apis(resp.items, type='validating_web_hook')


class Apiextension(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.ApiextensionsV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         context,
                         excluded_manifest_names
                         )

    def find_removed_apis_crds(self):
        resp = self.client.list_custom_resource_definition(watch=False)
        return self._find_all_removed_apis(resp.items, type='crd')        


class Apiregistration(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.ApiregistrationV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         context,
                         excluded_manifest_names
                         )

    def find_removed_apis_apiservices(self):
        resp = self.client.list_api_service(watch=False)
        return self._find_all_removed_apis(resp.items, type='apiservice')        


class Autoscaling(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.AutoscalingV2Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )

    def find_removed_apis_hpa(self):
        resp = self.client.list_horizontal_pod_autoscaler_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='horizontal_pod_autoscaler')


class Batch(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.BatchV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
 
    def find_removed_apis_cronjobs(self):
        resp = self.client.list_cron_job_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='cron_job')
    

class Coordination(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.CoordinationV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )

    def find_removed_apis_leases(self):
        resp = self.client.list_lease_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='lease')


class Certificates(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.CertificatesV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )

    def find_removed_apis_csr(self):
        resp = self.client.list_certificate_signing_request(watch=False)
        return self._find_all_removed_apis(resp.items, type='certificate_signing_request')


class Discovery(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client.DiscoveryV1Api.list_endpoint_slice_for_all_namespaces
        client_sig = client.DiscoveryV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
        
    def find_removed_apis_enpoint_slices(self):
        resp = self.client.list_endpoint_slice_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='endpoint_slice')


class Events(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.EventsV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
        
    def find_removed_apis_event(self):
        resp = self.client.list_event_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='event')


class Networking(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.NetworkingV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
 
    def find_removed_apis_ingresses(self):
        resp = self.client.list_ingress_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='ingress')
    
    def find_removed_apis_ingress_classes(self):
        resp = self.client.list_ingress_class(watch=False)
        return self._find_all_removed_apis(resp.items, type='ingress_class')


class Node(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.NodeV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
        
    def find_removed_apis_runtime_class(self):
        resp = self.client.list_runtime_class(watch=False)
        return self._find_all_removed_apis(resp.items, type='runtime_class')


class Policy(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.PolicyV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
 
    def find_removed_apis_pdb(self):
        resp = self.client.list_pod_disruption_budget_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='pod_disruption_budget')


class PolicyV1beta1(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.PolicyV1beta1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
    
    def find_removed_apis_pod_security_policy(self):
        resp = self.client.list_pod_security_policy(watch=False)
        return self._find_all_removed_apis(resp.items, type='pod_security_policy')

class RBAC(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.RbacAuthorizationV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
        
    def find_removed_apis_role(self):
        resp = self.client.list_role_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='role')

    def find_removed_apis_rolebinding(self):
        resp = self.client.list_role_binding_for_all_namespaces(watch=False)
        return self._find_all_removed_apis(resp.items, type='rolebinding')

    def find_removed_apis_cluster_role(self):
        resp = self.client.list_cluster_role(watch=False)
        return self._find_all_removed_apis(resp.items, type='cluster_role')
    def find_removed_apis_cluster_role_bindings(self):
        resp = self.client.list_cluster_role_binding(watch=False)
        return self._find_all_removed_apis(resp.items, type='cluster_role_binding')

class Scheduling(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.SchedulingV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
 
    def find_removed_apis_priority_classes(self):
        resp = self.client.list_priority_class(watch=False)
        return self._find_all_removed_apis(resp.items, type='priority_class')


class Storage(K8sApiClient):
    def __init__(self, removed_apis: Sequence[str], required_api: str, excluded_manifest_names=[], context=""):
        client_sig = client.StorageV1Api
        super().__init__(client_sig,
                         removed_apis,
                         required_api,
                         excluded_manifest_names,
                         context
                         )
        
    def find_removed_apis_csi_drivers(self):
        resp = self.client.list_csi_driver(watch=False)
        return self._find_all_removed_apis(resp.items, type='csi_driver')
    def find_removed_apis_csi_nodes(self):
        removed_apis = []
        try:
            resp = self.client.list_csi_node(watch=False)
            removed_apis = self._find_all_removed_apis(resp.items, type='csi_node')
        except ValueError as e:
            # Client errors when node has no drivers installed
            # https://github.com/kubernetes-client/python/issues/1909
            pass

        return removed_apis

    def find_removed_apis_storage_classes(self):
        resp = self.client.list_storage_class(watch=False)
        return self._find_all_removed_apis(resp.items, type='storage_class')
    def find_removed_apis_volume_attachments(self):
        resp = self.client.list_volume_attachment(watch=False)
        return self._find_all_removed_apis(resp.items, type='volume_attachment')