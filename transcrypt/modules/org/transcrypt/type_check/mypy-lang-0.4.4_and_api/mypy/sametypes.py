from typing import Sequence

from mypy.types import (
    Type, UnboundType, ErrorType, AnyType, NoneTyp, Void, TupleType, UnionType, CallableType,
    TypeVarType, Instance, TypeVisitor, ErasedType, TypeList, Overloaded, PartialType,
    DeletedType, UninhabitedType, TypeType
)


def is_same_type(left: Type, right: Type) -> bool:
    """Is 'left' the same type as 'right'?"""

    if isinstance(right, UnboundType):
        # Make unbound types same as anything else to reduce the number of
        # generated spurious error messages.
        return True
    else:
        # Simplify types to canonical forms.
        #
        # There are multiple possible union types that represent the same type,
        # such as Union[int, bool, str] and Union[int, str]. Also, some union
        # types can be simplified to non-union types such as Union[int, bool]
        # -> int. It would be nice if we always had simplified union types but
        # this is currently not the case, though it often is.
        left = simplify_union(left)
        right = simplify_union(right)

        return left.accept(SameTypeVisitor(right))


def simplify_union(t: Type) -> Type:
    if isinstance(t, UnionType):
        return UnionType.make_simplified_union(t.items)
    return t


def is_same_types(a1: Sequence[Type], a2: Sequence[Type]) -> bool:
    if len(a1) != len(a2):
        return False
    for i in range(len(a1)):
        if not is_same_type(a1[i], a2[i]):
            return False
    return True


class SameTypeVisitor(TypeVisitor[bool]):
    """Visitor for checking whether two types are the 'same' type."""

    def __init__(self, right: Type) -> None:
        self.right = right

    # visit_x(left) means: is left (which is an instance of X) the same type as
    # right?

    def visit_unbound_type(self, left: UnboundType) -> bool:
        return True

    def visit_error_type(self, left: ErrorType) -> bool:
        return False

    def visit_type_list(self, t: TypeList) -> bool:
        assert False, 'Not supported'

    def visit_any(self, left: AnyType) -> bool:
        return isinstance(self.right, AnyType)

    def visit_void(self, left: Void) -> bool:
        return isinstance(self.right, Void)

    def visit_none_type(self, left: NoneTyp) -> bool:
        return isinstance(self.right, NoneTyp)

    def visit_uninhabited_type(self, t: UninhabitedType) -> bool:
        return isinstance(self.right, UninhabitedType)

    def visit_erased_type(self, left: ErasedType) -> bool:
        # We can get here when isinstance is used inside a lambda
        # whose type is being inferred. In any event, we have no reason
        # to think that an ErasedType will end up being the same as
        # any other type, even another ErasedType.
        return False

    def visit_deleted_type(self, left: DeletedType) -> bool:
        return isinstance(self.right, DeletedType)

    def visit_instance(self, left: Instance) -> bool:
        return (isinstance(self.right, Instance) and
                left.type == self.right.type and
                is_same_types(left.args, self.right.args))

    def visit_type_var(self, left: TypeVarType) -> bool:
        return (isinstance(self.right, TypeVarType) and
                left.id == self.right.id)

    def visit_callable_type(self, left: CallableType) -> bool:
        # FIX generics
        if isinstance(self.right, CallableType):
            cright = self.right
            return (is_same_type(left.ret_type, cright.ret_type) and
                    is_same_types(left.arg_types, cright.arg_types) and
                    left.arg_names == cright.arg_names and
                    left.arg_kinds == cright.arg_kinds and
                    left.is_type_obj() == cright.is_type_obj() and
                    left.is_ellipsis_args == cright.is_ellipsis_args)
        else:
            return False

    def visit_tuple_type(self, left: TupleType) -> bool:
        if isinstance(self.right, TupleType):
            return is_same_types(left.items, self.right.items)
        else:
            return False

    def visit_union_type(self, left: UnionType) -> bool:
        # XXX This is a test for syntactic equality, not equivalence
        if isinstance(self.right, UnionType):
            return is_same_types(left.items, self.right.items)
        else:
            return False

    def visit_overloaded(self, left: Overloaded) -> bool:
        if isinstance(self.right, Overloaded):
            return is_same_types(left.items(), self.right.items())
        else:
            return False

    def visit_partial_type(self, left: PartialType) -> bool:
        # A partial type is not fully defined, so the result is indeterminate. We shouldn't
        # get here.
        raise RuntimeError

    def visit_type_type(self, left: TypeType) -> bool:
        if isinstance(self.right, TypeType):
            return is_same_type(left.item, self.right.item)
        else:
            return False